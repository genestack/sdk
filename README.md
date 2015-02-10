# PythonSDK

### Documentation

   [Documentation](https://internal-dev.genestack.com/developers/index.html)

### Repo

  ```
  docs/                             - folder with documentation sources
  genestack/                        - folder with genestack library
  tests/                            - developer tests, require pytest to run.
  genestack-application-manager.py  - script to connect to application-manager (installed as script with genestack)
  genestack-user-setup.py           - script to setup user (installed as script with genestack)
  local_settings_sample.xml         - sample settings file for local developer
  setup.py                          - installation setup for genestack library
  ```


### Generate docs

 - install sphinx http://sphinx-doc.org/
 - `cd docs`
 - `make html`

 **Note!** Make docs use script `make_shell_docs.py` that generates documentation files for shell scripts(genestack-user-setup.rst, genestack-application-manager.rst). 
 app-manager_usage.rst is not included to index, it is required for `make_shell_docs.py`
