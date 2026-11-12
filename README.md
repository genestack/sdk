# Library `odm_sdk`

### Documentation

   [stable](https://odm.demo.genestack.com/user-docs/tools/odm-sdk/installation/)

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

### Build and publish

The `Makefile` builds the `Dockerfile`'s targets:

```bash
make test OPENAPI_VERSION=1.0.0-3988   # tox run-parallel (pytest) against that odm-api
make push OPENAPI_VERSION=1.0.0-3988 IMAGE_VERSION=1.0.0-4454   # the sdist, uploaded without tests
```

`make push` uploads to PyPI for a release `IMAGE_VERSION` (X.Y.Z) and to TestPyPI otherwise, with `PYPI_TOKEN` or `PYPI_TOKEN_TEST` from `.secret` or the environment. `OPENAPI_VERSION` must be an odm-api version on PyPI or TestPyPI. CI also runs `make sonarcloud`; `make help` lists every target.
