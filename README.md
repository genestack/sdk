# PythonSDK

## Ducumnetation

   [x Missed documentation link is here x]()

## Repo

  ```
  docs/                             - folder with documentation
  genestack/                        - folder with genestack library
  tests/                            - developer tests, require pytest to run.
  genestack-application-manager.py  - script to connect to application-manager (installed as script with genestack)
  genestack-user-setup.py           - script to setup user (installed as script with genestack)
  setup.py                          - installation setup for genestack library
  local_settings_sample.xml         - sample settings file for local developer
  ```


## Generate docs


   To make docs you need to install sphinx http://sphinx-doc.org/

   `cd docs`
   
   `make html`

   **Note!** Make docs use script `make_shell_docs.py` that generates documentation files for shell
    scripts(genestack-user-setup.rst, genestack-application-manager.rst).  app-manager_usage.rst is not included to index, it is required for `make_shell_docs.py`



