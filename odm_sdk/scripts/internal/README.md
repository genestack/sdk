# README.md

The directory contains scripts that are designed for generating source files for some predefined dictionaries, which are
uploaded by the [init-image](https://github.com/genestack/init-image). The source files can be found in the `odm-init`
S3 bucket. These scripts serve as a backup solution in case the original data is lost.

## Scripts Description

### generate_gene_dictionaries.py

This script is used for generating gene dictionaries. It requires access to [Ensembl FTP](https://ftp.ensembl.org/)
and [NCBI FTP](https://ftp.ncbi.nlm.nih.gov/).
Currently, we only upload dictionaries that are extended with gene synonyms from NCBI (
see `dictionaries/gene-dictionaries/` in the`odm-init` bucket). To generate source files only for NCBI-patched
dictionaries you can specify `-ncbi` option.

### generate_unit_dictionaries.py

This script generates unit vocabularies. It accepts `--destination-path` as an optional parameter, allowing users to
specify the path where the generated dictionaries should be saved.

### Additional Source File

There is also a source file named `/data/disease_extension.csv` used for disease ontology extension.
