# Library `odm_sdk`

### Documentation

   [stable](http://genestack-client.readthedocs.io/en/stable/)

### Installation

```shell
python3 -m pip install odm-sdk
```

### Usage

```shell
odm-user-setup init
```

### Generate documentation files

```shell
python3 -m pip install -r requirements-docs.txt
cd docs
make html
```

**Note!** `make` use script `make_shell_docs.py` that generates documentation for shell applications

### Repo structure

```
docs/                             - folder with documentation sources
odm_sdk/                          - folder with library and tests
setup.py                          - installation setup for odm_sdk library
```
