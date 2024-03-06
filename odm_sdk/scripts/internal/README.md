# README.md

These scripts are designed for generating source files for some predefined dictionaries, which are uploaded by the
initial image. The source files can be found in the `odm-init` S3 buckets. These scripts serve as a backup solution in
case the original data is lost.

## Scripts Description

### generate_gene_dictionaries.py

This script is used for generating gene dictionaries. It does not require any input parameters. However, it requires
access to [Ensembl FTP](https://ftp.ensembl.org/) and [NCBI FTP](https://ftp.ncbi.nlm.nih.gov/). Currently, we
only upload dictionaries that are extended with gene synonyms from NCBI (see `dictionaries/gene-dictionaries/` in the
`odm-init` bucket).

### generate_unit_dictionaries.py

This script generates unit vocabularies. It accepts `--destination-path` as an optional parameter, allowing users to
specify the path where the generated dictionary should be saved.

### Additional Source File

There is also a source file named `/data/disease_extension.csv` used for disease ontology extension.
