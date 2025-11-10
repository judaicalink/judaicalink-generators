import argparse
import json
import toml

try:
    from rdf_generator.generators.csv_generator import CsvGenerator
except ImportError as e:
    raise ImportError(
        "rdf_generator package is required. Install it via 'pip install git+https://github.com/judaicalink/rdf_generator'"
    ) from e


def load_mapping(path: str):
    """Load mapping from JSON or TOML file."""
    if path.endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    if path.endswith(".toml"):
        with open(path, "r", encoding="utf-8") as f:
            return toml.load(f)
    raise ValueError("Mapping file must be JSON or TOML")


def main():
    parser = argparse.ArgumentParser(description="Generate RDF from CSV using a mapping file")
    parser.add_argument("mapping", help="Path to mapping file (.json or .toml)")
    parser.add_argument("csv", help="Input CSV file")
    parser.add_argument("output", help="Output Turtle file")
    args = parser.parse_args()

    mapping = load_mapping(args.mapping)
    generator = CsvGenerator(mapping)
    generator.generate(args.csv)
    generator.graph.serialize(destination=args.output, format="turtle")


if __name__ == "__main__":
    main()
