# JudaicaLink Generator

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






