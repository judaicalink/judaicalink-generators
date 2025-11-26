# jl_generators/management/commands/jlgen.py
from django.core.management.base import BaseCommand
from pathlib import Path
from django.utils import timezone
from jl_generators.models import Generator, Run
import importlib, json, subprocess, shlex, os


class Command(BaseCommand):
    help = "Lists generators, executes them, loads them into Fuseki, and checks cron jobs."

    def add_arguments(self, parser):
        sub = parser.add_subparsers(dest="cmd")
        sub.add_parser("list")

        p_run = sub.add_parser("run")
        p_run.add_argument("--slug", help="single generator (slug)")
        p_run.add_argument("--load", action="store_true", help="load into Fuseki after generation")

        sub.add_parser("run_all")
        sub.add_parser("status")

        p_load = sub.add_parser("load")
        p_load.add_argument("--slug")
        p_load.add_argument("--only-newer", action="store_true")

        sub.add_parser("check")  # cron: checks DB config/enable and triggers if necessary

    def handle(self, *args, **opts):
        cmd = opts["cmd"]
        if cmd == "list":
            self._list()
        elif cmd == "run":
            self._run(slug=opts.get("slug"), do_load=opts.get("load"))
        elif cmd == "run_all":
            gens = Generator.objects.filter(enabled=True).values_list("slug", flat=True)
            for slug in gens:
                self._run(slug=slug, do_load=False)
        elif cmd == "status":
            self._status()
        elif cmd == "load":
            self._load(slug=opts.get("slug"), only_newer=opts.get("only_newer"))
        elif cmd == "check":
            self._check()
        else:
            self.stdout.write(self.style.ERROR("Unknown command"))

    def _list(self):
        for g in Generator.objects.all():
            self.stdout.write(f"- {g.slug} {'(disabled)' if not g.enabled else ''}")

    def _dataset_root(self, slug: str) -> Path:
        return Path(__file__).resolve().parents[4] / "datasets" / slug

    def _import_dataset_generator(self, slug: str):
        mod = importlib.import_module(f"datasets.{slug}.scripts.generator")
        return mod.Generator

    def _run(self, slug: str | None, do_load: bool = False):
        slugs = [slug] if slug else list(Generator.objects.filter(enabled=True).values_list("slug", flat=True))
        for s in slugs:
            gconf = Generator.objects.get(slug=s)
            ds_root = self._dataset_root(s)
            GenClass = self._import_dataset_generator(s)
            gen = GenClass(ds_root)
            res = gen.run()
            run = Run.objects.create(
                generator=gconf,
                status=res.get("status", "error"),
                triples=res.get("triples", 0),
                artifact_ttl=res.get("public_ttl", ""),
                log=res.get("traceback", ""),
                finished_at=timezone.now(),
            )
            if do_load and res.get("status") == "success":
                self._loader_load(s, ds_root, res.get("ttl"))

            msg = f"[{s}] {res['status']} triples={res.get('triples', 0)}"
            self.stdout.write(self.style.SUCCESS(msg) if res["status"] == "success" else self.style.ERROR(msg))

    def _loader_load(self, slug: str, ds_root: Path, ttl_path: str | None):
        if not ttl_path: return
        # uses judaicalink_loader to load TTL into Fuseki
        fuseki_url = os.environ.get("JL_FUSEKI_URL")  # e.g. http://localhost:3030/judaicalink
        if not fuseki_url:
            self.stdout.write(self.style.WARNING("JL_FUSEKI_URL not set – skip load"))
            return
        cmd = f"python -m loader.loader --dataset {slug} --ttl {shlex.quote(ttl_path)} --endpoint {shlex.quote(fuseki_url)}"
        subprocess.run(cmd, shell=True, check=False)

    def _status(self):
        for g in Generator.objects.all():
            last = g.runs.order_by("-id").first()
            stamp = last.finished_at.isoformat() if last else "—"
            icon = "✅" if last and last.status == "success" else "❌" if last else "•"
            self.stdout.write(f"{icon} {g.slug}  {stamp}")

    def _load(self, slug: str | None, only_newer: bool = False):
        # Optional: Check the timestamp of the last loaded graph version for each data record
        # and call _loader_load if a newer TTL exists.
        pass

    def _check(self):
        # Cron: simple logic – start all enabled generators,
        # in v2 you can interpret BYDAY/BYHOUR etc. from the database.
        self._run(slug=None, do_load=False)
