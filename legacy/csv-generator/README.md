# Generic CSV Generator

This generator converts CSV data into RDF using a mapping file. The mapping can be provided in JSON or TOML format and describes which columns of the CSV file correspond to which ontology properties. The conversion relies on the [`rdf_generator`](https://github.com/judaicalink/rdf_generator) library.

## Usage

Install the requirements listed in the repository and install the `rdf_generator` library:

```bash
pip install -r ../../requirements.txt
pip install git+https://github.com/judaicalink/rdf_generator
```

Run the generator by providing a mapping file, a CSV input file and the name of the output file:

```bash
python generator.py mapping.toml input.csv output.ttl
```

The resulting Turtle file will be written to the provided output path.
