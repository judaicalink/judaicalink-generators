# generators/loader.py
from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import requests

# Optional: rdflib for counting triples
try:
    from rdflib import Graph as RDFGraph  # type: ignore
except Exception:  # pragma: no cover
    RDFGraph = None  # type: ignore

# ---------------------------------------
# Configuration
# ---------------------------------------
ENV_FUSEKI_URL = "JL_FUSEKI_URL"  # e.g. http://localhost:3030/judaicalink
ENV_FUSEKI_USER = "JL_FUSEKI_USER"
ENV_FUSEKI_PASSWORD = "JL_FUSEKI_PASSWORD"
ENV_USE_LEGACY_LOADER = "JL_USE_LEGACY_LOADER"  # "1" -> python -m loader.loader
ENV_REQUEST_TIMEOUT = "JL_HTTP_TIMEOUT"  # Seconds (default 60)


# ---------------------------------------
# Data types
# ---------------------------------------
@dataclass
class LoadResult:
    slug: str
    ttl_path: str
    endpoint: str
    graph: Optional[str]
    replaced: bool
    status: str  # "success" | "skipped" | "error"
    triples: Optional[int]  # counted number (None oif unknown)
    message: str
    loaded_at: float


# ---------------------------------------
# Utilities
# ---------------------------------------
def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """
    Compute SHA256 hash of a file.
    :param path: Path to file
    :param chunk_size: Read chunk size
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def _state_file(ttl_path: Path) -> Path:
    """
    Get path to state file for given TTL path.
    Stored in ../tmp/.load_state.json relative to TTL file.
    :param ttl_path: Path to TTL file
    :return: Path to state file
    """
    # Save state file in tmp dir
    os.mkdir("../tmp") if not Path("../tmp").exists() else None
    return ttl_path.parent / "../tmp/.load_state.json"


def _load_state(state_path: Path) -> dict:
    """
    Load state from JSON file.
    :param state_path: Path to state file
    :return: State dict
    """
    if state_path.exists():
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_state(state_path: Path, state: dict) -> None:
    """
    Save state to JSON file.
    2-space indent, UTF-8.
    :param state_path: Path to state file
    :param state: State dict
    """
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _should_load_newer(ttl_path: Path, slug: str, only_newer: bool) -> Tuple[bool, str]:
    """
    Determine if loading is necessary. If only_newer=True,
    compare SHA256 and mtime with previously saved state.
    :param ttl_path: Path to TTL file
    :param slug: Dataset slug (for state tracking)
    :param only_newer: Whether to check for newer
    :return: (should_load: bool, reason: str)
    """
    if not only_newer:
        return True, "only_newer disabled"

    state_path = _state_file(ttl_path)
    state = _load_state(state_path)
    prev = state.get(slug, {})

    current_hash = _sha256_file(ttl_path)
    current_mtime = int(ttl_path.stat().st_mtime)

    if prev.get("sha256") == current_hash and prev.get("mtime") == current_mtime:
        return False, "unchanged (hash & mtime match)"

    return True, "changed (hash or mtime differs)"


def _estimate_triples(ttl_path: Path) -> Optional[int]:
    """
    Fast, optional triple count. Prefers rdflib,
    falls back to simple heuristic (lines ending with ' .').
    :param ttl_path: Path to TTL file
    :return: Estimated triple count or None if unknown
    """
    if RDFGraph is not None:
        try:
            g = RDFGraph()
            g.parse(str(ttl_path), format="turtle")
            return len(g)
        except Exception:
            pass

    # Fallback (Heuristics)
    try:
        cnt = 0
        with ttl_path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.rstrip().endswith(" ."):
                    cnt += 1
        return cnt or None
    except Exception:
        return None


def _normalize_fuseki_endpoint(base: str) -> str:
    """
    Normalizes Fuseki dataset endpoint to Graph Store Protocol /data endpoint.
    Accepts for example:
      - http://host:3030/ds
      - http://host:3030/ds/
      - http://host:3030/ds/data
      - http://host:3030/ds/data/
    and returns the Graph Store Protocol Base /data.
    :param base: Base Fuseki dataset URL
    :return: Normalized /data endpoint URL
    """
    base = base.rstrip("/")
    if base.endswith("/data"):
        return base
    return base + "/data"


def _http_timeout() -> int:
    """
    Get HTTP request timeout from environment or default to 60 seconds.
    :return: Timeout in seconds
    """
    try:
        return int(os.environ.get(ENV_REQUEST_TIMEOUT, "60"))
    except Exception:
        return 60


# ---------------------------------------
# HTTP (Graph Store Protocol)
# ---------------------------------------
def _fuseki_delete_graph(data_endpoint: str, graph_uri: str, auth: Optional[Tuple[str, str]]) -> None:
    """
    DELETE deletes the Named Graph in Fuseki.
    :param data_endpoint: Fuseki /data endpoint
    :param graph_uri: Named Graph URI to delete
    :param auth: Optional Basic Auth tuple (user, password)
    :return: None
    """
    resp = requests.delete(
        data_endpoint,
        params={"graph": graph_uri},
        auth=auth,
        timeout=_http_timeout(),
    )
    # Accept 200 or 204 are OK; 404 is ignored (missing graph)
    if resp.status_code not in (200, 204, 404):
        raise RuntimeError(f"DELETE graph failed ({resp.status_code}): {resp.text[:500]}")


def _fuseki_put_graph(data_endpoint: str, graph_uri: str, turtle: bytes, auth: Optional[Tuple[str, str]]) -> None:
    """
    PUT loads/replaces a Named Graph in Fuseki.
    :param data_endpoint: Fuseki /data endpoint
    :param graph_uri: Named Graph URI to load
    :param turtle: Turtle data as bytes
    :param auth: Optional Basic Auth tuple (user, password)
    :return: None
    """
    # PUT loads/replaces the graph
    resp = requests.put(
        data_endpoint,
        params={"graph": graph_uri},
        data=turtle,
        headers={"Content-Type": "text/turtle"},
        auth=auth,
        timeout=_http_timeout(),
    )
    if resp.status_code not in (200, 201, 204):
        raise RuntimeError(f"PUT graph failed ({resp.status_code}): {resp.text[:500]}")


def _fuseki_post_default(data_endpoint: str, turtle: bytes, auth: Optional[Tuple[str, str]], append: bool) -> None:
    """
    Load default graph in Fuseki: POST (append) or PUT (replace) to ?default.
    Usually Fuseki setups allow POST -> Append in Default Graph.
    :param data_endpoint: Fuseki /data endpoint
    :param turtle: Turtle data as bytes
    :param auth: Optional Basic Auth tuple (user, password)
    :param append: If True, use POST to append; if False, use PUT to replace
    :return: None
    """
    if append:
        resp = requests.post(
            data_endpoint,
            params={"default": ""},
            data=turtle,
            headers={"Content-Type": "text/turtle"},
            auth=auth,
            timeout=_http_timeout(),
        )
        if resp.status_code not in (200, 201, 204):
            raise RuntimeError(f"POST default failed ({resp.status_code}): {resp.text[:500]}")
    else:
        resp = requests.put(
            data_endpoint,
            params={"default": ""},
            data=turtle,
            headers={"Content-Type": "text/turtle"},
            auth=auth,
            timeout=_http_timeout(),
        )
        if resp.status_code not in (200, 201, 204):
            raise RuntimeError(f"PUT default failed ({resp.status_code}): {resp.text[:500]}")


# ---------------------------------------
# Legacy Loader Wrapper (optional)
# ---------------------------------------
def _run_legacy_loader(slug: str, ttl_path: Path, endpoint: str) -> int:
    """
    Fallback: use existing judaicalink-loader as subprocess.
    Expects: python -m loader.loader --dataset <slug> --ttl <file> --endpoint <fuseki>
    :param slug: Dataset slug
    :param ttl_path: Path to TTL file
    :param endpoint: Fuseki endpoint
    :return: Subprocess return code
    """
    cmd = f"python -m loader.loader --dataset {shlex.quote(slug)} --ttl {shlex.quote(str(ttl_path))} --endpoint {shlex.quote(endpoint)}"
    return subprocess.call(cmd, shell=True)


# ---------------------------------------
# Public API
# ---------------------------------------
def load_to_fuseki(
        slug: str,
        ttl_path: str | Path,
        endpoint: Optional[str] = None,
        graph: Optional[str] = None,
        replace: bool = True,
        only_newer: bool = False,
        use_legacy: Optional[bool] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
) -> LoadResult:
    """
    Load a Turtle file into a Fuseki dataset via HTTP Graph Store Protocol or legacy loader.
    :param slug: Dataset slug (for state file & legacy CLI)
    :param ttl_path: Path to Turtle file
    :param endpoint: Fuseki dataset base (without /data); if None -> ENV JL_FUSEKI_URL
    :param graph: Named Graph URI; None => Default Graph
    :param replace: True => replace graph; False => append to graph
    :param only_newer: True => only load if file has changed (hash/mtime)
    :param use_legacy: True => force legacy loader; False => HTTP; None => ENV JL_USE_LEGACY_LOADER
    :param username: Basic Auth username; if None -> ENV JL_FUSEKI_USER
    :param password: Basic Auth password; if None -> ENV JL_FUSEKI_PASSWORD
    :return: LoadResult
    """
    start_ts = time.time()
    ttl = Path(ttl_path)
    if not ttl.exists():
        raise FileNotFoundError(f"TTL not found: {ttl}")

    endpoint = endpoint or os.environ.get(ENV_FUSEKI_URL, "http://localhost:3030/judaicalink/query").strip()
    if not endpoint:
        raise RuntimeError(f"Keine Fuseki-URL gesetzt (ENV {ENV_FUSEKI_URL}).")

    username = username if username is not None else os.environ.get(ENV_FUSEKI_USER)
    password = password if password is not None else os.environ.get(ENV_FUSEKI_PASSWORD)
    auth = (username, password) if username and password else None

    # only_newer?
    do_load, reason = _should_load_newer(ttl, slug, only_newer)
    if not do_load:
        return LoadResult(
            slug=slug,
            ttl_path=str(ttl),
            endpoint=endpoint,
            graph=graph,
            replaced=False,
            status="skipped",
            triples=_estimate_triples(ttl),
            message=f"Skip (only_newer): {reason}",
            loaded_at=time.time(),
        )

    # Legacy?
    if use_legacy is None:
        use_legacy = os.environ.get(ENV_USE_LEGACY_LOADER, "").strip() == "1"

    triples = _estimate_triples(ttl)

    if use_legacy:
        rc = _run_legacy_loader(slug, ttl, endpoint)
        if rc != 0:
            raise RuntimeError(f"Legacy loader exited with code {rc}")
        _persist_state(ttl, slug)
        return LoadResult(
            slug=slug,
            ttl_path=str(ttl),
            endpoint=endpoint,
            graph=graph,
            replaced=replace,
            status="success",
            triples=triples,
            message="Loaded via legacy loader",
            loaded_at=time.time(),
        )

    # HTTP Graph Store Protocol
    data_endpoint = _normalize_fuseki_endpoint(endpoint)
    turtle_bytes = ttl.read_bytes()

    if graph:
        if replace:
            # Delete & set new (more robust for many triples)
            _fuseki_delete_graph(data_endpoint, graph, auth)
            _fuseki_put_graph(data_endpoint, graph, turtle_bytes, auth)
        else:
            # Attach: PUT overwrites; for Append need SPARQL Update INSERT DATA.
            # Simple solution: POST to /update with INSERT DATA.
            _sparql_insert_data(endpoint, turtle_bytes, graph, auth)
    else:
        # Default Graph
        _fuseki_post_default(data_endpoint, turtle_bytes, auth, append=(not replace))

    _persist_state(ttl, slug)

    return LoadResult(
        slug=slug,
        ttl_path=str(ttl),
        endpoint=endpoint,
        graph=graph,
        replaced=replace,
        status="success",
        triples=triples,
        message="Loaded via HTTP Graph Store",
        loaded_at=time.time(),
    )


def _persist_state(ttl: Path, slug: str) -> None:
    """"
    Persist load state (SHA256, mtime, loaded_at) for given TTL and slug.
    :param ttl: Path to TTL file
    :param slug: Dataset slug
    :return: None
    """
    state_path = _state_file(ttl)
    state = _load_state(state_path)
    state[slug] = {
        "sha256": _sha256_file(ttl),
        "mtime": int(ttl.stat().st_mtime),
        "loaded_at": int(time.time()),
    }
    _save_state(state_path, state)


def _sparql_insert_data(
        endpoint_base: str,
        turtle_bytes: bytes,
        graph_uri: str,
        auth: Optional[Tuple[str, str]],
) -> None:
    """
    Execute INSERT DATA on named graph.
    Uses /update endpoint (SPARQL update). Expects Turtle in the request,
    converts minimally by embedding the bytes as a string.
    Note: This is not ideal for very large TTLs – in that case, it's better to use
    a replacement strategy.
    :param endpoint_base: Fuseki dataset base URL
    :param turtle_bytes: Turtle data as bytes
    :param graph_uri: Named Graph URI
    :param auth: Optional Basic Auth tuple (user, password)
    :return: None
    """
    update_endpoint = endpoint_base.rstrip("/") + "/update"

    # Embedd Turtle as string (cautious with '"""' quotes)
    turtle_str = turtle_bytes.decode("utf-8", errors="ignore")
    sparql = f"INSERT DATA {{ GRAPH <{graph_uri}> {{\n{turtle_str}\n}} }}"

    resp = requests.post(
        update_endpoint,
        data={"update": sparql},
        auth=auth,
        timeout=_http_timeout(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if resp.status_code not in (200, 204):
        raise RuntimeError(f"SPARQL INSERT DATA failed ({resp.status_code}): {resp.text[:500]}")


# --- subject specific UPSERT in common metadata graph ---

def upsert_metadata_graph(
        slug: str,
        ttl_path: str | Path,
        endpoint: Optional[str] = None,
        graph: str = "http://data.judaicalink.org/datasets",
        subject: Optional[str] = None,
        only_newer: bool = False,
        username: Optional[str] = None,
        password: Optional[str] = None,
) -> LoadResult:
    """
    Replaces ONLY the metadata for `subject` within the shared named graph `graph`.
    Other subjects in `graph` remain unchanged.
    Expectation: The TTL file contains ONLY triples for the desired subject (and its blank nodes).
    :param slug: Dataset slug (for state file)
    :param ttl_path: Path to Turtle file
    :param endpoint: Fuseki dataset base (without /data); if None -> ENV JL_FUSEKI_URL
    :param graph: Named Graph URI (default: common metadata graph)
    :param subject: Subject URI to upsert; if None -> derived from slug
    :param only_newer: True => only load if file has changed (hash/mtime)
    :param username: Basic Auth username; if None -> ENV JL_FUSEKI_USER
    :param password: Basic Auth password; if None -> ENV JL_FUSEKI_PASSWORD
    :return: LoadResult
    """
    start_ts = time.time()
    ttl = Path(ttl_path)
    if not ttl.exists():
        raise FileNotFoundError(f"TTL not found: {ttl}")

    endpoint = endpoint or os.environ.get(ENV_FUSEKI_URL, "").strip()
    if not endpoint:
        raise RuntimeError(f"Fuseki URL not set (ENV {ENV_FUSEKI_URL}).")

    username = username if username is not None else os.environ.get(ENV_FUSEKI_USER)
    password = password if password is not None else os.environ.get(ENV_FUSEKI_PASSWORD)
    auth = (username, password) if username and password else None

    # Derive subject: either explicitly or from filename/slug
    if not subject:
        # Standard: http://data.judaicalink.org/datasets/<slug>
        subject = f"http://data.judaicalink.org/datasets/{slug}"

    # only_newer?
    do_load, reason = _should_load_newer(ttl, slug, only_newer)
    if not do_load:
        return LoadResult(
            slug=slug,
            ttl_path=str(ttl),
            endpoint=endpoint,
            graph=graph,
            replaced=False,
            status="skipped",
            triples=_estimate_triples(ttl),
            message=f"Skip (only_newer): {reason}",
            loaded_at=time.time(),
        )

    # 1) DELETE only for this subject (including directly linked blank nodes)
    # Two-phase deletion:
    # (a) all triples with <subject> as the subject
    # (b) all triples with blank nodes as the subject that function as objects of <subject> (one level)
    update_endpoint = endpoint.rstrip("/") + "/update"
    delete_subj = f"""
    DELETE WHERE {{
      GRAPH <{graph}> {{
        <{subject}> ?p ?o .
      }}
    }}
    """
    # Blank node triples attached to <subject> (one level)
    delete_bnodes = f"""
    DELETE {{
      GRAPH <{graph}> {{
        ?bn ?p2 ?o2 .
      }}
    }}
    WHERE {{
      GRAPH <{graph}> {{
        <{subject}> ?p ?bn .
        FILTER(isBlank(?bn))
        ?bn ?p2 ?o2 .
      }}
    }}
    """

    for upd in (delete_subj, delete_bnodes):
        resp = requests.post(
            update_endpoint,
            data={"update": upd},
            auth=auth,
            timeout=_http_timeout(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code not in (200, 204):
            raise RuntimeError(f"SPARQL UPDATE failed ({resp.status_code}): {resp.text[:500]}")

    # 2) INSERT DATA with the new triples (from the TTL file)
    # Turtle with @prefix is not allowed in INSERT DATA.
    # -> We parse the file and serialize for N triples (without prefixes).
    if RDFGraph is None:
        raise RuntimeError("rdflib (RDFGraph) is required for upsert_metadata_graph")

    g = RDFGraph()
    g.parse(str(ttl), format="turtle")

    nt_str = g.serialize(format="nt")
    if isinstance(nt_str, bytes):
        nt_str = nt_str.decode("utf-8")

    insert = f"INSERT DATA {{ GRAPH <{graph}> {{\n{nt_str}\n}} }}"
    resp = requests.post(
        update_endpoint,
        data={"update": insert},
        auth=auth,
        timeout=_http_timeout(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if resp.status_code not in (200, 204):
        raise RuntimeError(f"SPARQL INSERT DATA failed ({resp.status_code}): {resp.text[:500]}")

    _persist_state(ttl, slug)

    return LoadResult(
        slug=slug,
        ttl_path=str(ttl),
        endpoint=endpoint,
        graph=graph,
        replaced=False,
        status="success",
        triples=_estimate_triples(ttl),
        message=f"Upsert in metadata graph <{graph}> for subject <{subject}>",
        loaded_at=time.time(),
    )


# ---------------------------------------
# CLI
# ---------------------------------------
def _cli(argv: list[str]) -> int:
    """
    Command-line interface for loading TTL into Fuseki.
    :param argv: Command-line arguments
    :return: Exit code
    """
    import argparse

    p = argparse.ArgumentParser(description="Load a TTL into Fuseki.")
    p.add_argument("--slug", required=True, help="Dataset slug (for state & legacy CLI)")
    p.add_argument("--ttl", required=True, help="Path to .ttl file")
    p.add_argument("--endpoint", default=os.environ.get(ENV_FUSEKI_URL, ""), help="Fuseki dataset base (without /data)")
    p.add_argument("--graph", default=None, help="Named graph URI (omit for default graph)")
    p.add_argument("--append", action="store_true", help="Append instead of replace")
    p.add_argument("--only-newer", action="store_true", help="Skip if file unchanged (hash & mtime)")
    p.add_argument("--legacy", action="store_true", help="Force legacy loader (python -m loader.loader)")
    p.add_argument("--user", default=os.environ.get(ENV_FUSEKI_USER), help="Basic auth user")
    p.add_argument("--password", default=os.environ.get(ENV_FUSEKI_PASSWORD), help="Basic auth password")

    args = p.parse_args(argv)

    res = load_to_fuseki(
        slug=args.slug,
        ttl_path=args.ttl,
        endpoint=args.endpoint or None,
        graph=args.graph,
        replace=not args.append,
        only_newer=args.only_newer,
        use_legacy=True if args.legacy else None,
        username=args.user,
        password=args.password,
    )
    print(json.dumps(res.__dict__, ensure_ascii=False, indent=2))
    return 0 if res.status in ("success", "skipped") else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_cli(sys.argv[1:]))
