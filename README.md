# JudaicaLink Generators

[![Open Source? Yes!](https://badgen.net/badge/Open%20Source%20%3F/Yes%21/blue?icon=github)](https://github.com/Naereen/badges/)
![license](https://badgen.net/badge/license/MIT/blue)
![Maintenance](https://img.shields.io/maintenance/yes/2025)

[![made-with-Markdown](https://img.shields.io/badge/Made%20with-Markdown-1f425f.svg)](http://commonmark.org)

![github](https://badgen.net/badge/icon/github?icon=github&label)
![release](https://badgen.net/github/release/judaicalink/judaicalink-generators?color=green)
![releases](https://badgen.net/github/releases/judaicalink/judaicalink-generators)
![stars](https://badgen.net/github/stars/judaicalink/judaicalink-generators)![forks](https://badgen.net/github/forks/judaicalink/judaicalink-generators)
![issues](https://badgen.net/github/issues/judaicalink/judaicalink-generators)
![commits](https://badgen.net/github/commits/judaicalink/judaicalink-generators)
![last-commit](https://badgen.net/github/last-commit/judaicalink/judaicalink-generators)
![branches](https://badgen.net/github/branches/judaicalink/judaicalink-generators)
![contributors](https://badgen.net/github/contributors/judaicalink/judaicalink-generators)

![wiki](https://badgen.net/badge/icon/wiki?icon=wiki&label)
[![Documentation Status](https://readthedocs.org/projects/judaicalink-docs/badge/?version=latest)](http://judaicalink-docs.readthedocs.io/?badge=latest)

![discord](https://badgen.net/badge/icon/discord?icon=discord&label)
![Discord](https://img.shields.io/discord/696646598868074576)

This repository is part of the JudaicaLink project (https://judaicalink.org/), which aims to create a comprehensive knowledge base for Jewish studies by integrating various datasets and resources.
It is used to generate the datasets for the JudaicaLink knowledge graph.

## Overview

Each folder in this repository corresponds to a specific dataset or component of the JudaicaLink knowledge base.
The folder names is the slug of the dataset.

## Structure

- `<dataset-name>/`: Contains the source code, data files, and documentation for a specific dataset.
- <dataset-name>/source/: Contains source files used to generate the dataset.
- <dataset-name>/scripts/: Contains scripts used to process the data and generate RDF files.
- <dataset-name>/output/: Contains the generated RDF files for the dataset or zipped datasets.
- <dataset-name>/README.md: Documentation specific to the dataset, including data sources, processing steps, and usage instructions.
- <dataset-name>/tmp/: Temporary files generated during the data processing.



This repository contains the description and materials regarding the content generated for JudaicaLink knowledge base. 
This folder contains all the datasets created for the JudaicaLink as well as the source code and description of the process. 

Every dataset corresponds to a name graph that can later on be accessed in the triple store. 
Datasets may consist of more than one data file since they might have been further expanded over time or may contain different data components. 

Users can download JudaicaLink datasets from the webpage of JudaicaLink . The datasets can also be browsed as Linked Open Data using Pubby (with DM2E extensions) as Web Frontend. Furthermore, a public SPARQL endpoint is available.
A generic CSV generator is available in `csv-generator` for converting CSV data based on a JSON or TOML mapping using the `rdf_generator` library.






