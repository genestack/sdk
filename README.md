# Python Client Library

### Documentation

   [Documentation](https://internal-dev.genestack.com/developers/index.html)

### Repo

  ```
  docs/                             - folder with documentation sources
  genestack/                        - folder with genestack library
  tests/                            - developer tests, require pytest to run.
  genestack-application-manager     - script to connect to application-manager (installed as script with genestack)
  genestack-user-setup              - script to setup user (installed as script with genestack)
  local_settings_sample.xml         - sample settings file for local developer
  setup.py                          - installation setup for genestack library
  ```

### Generate documentation files

 - install [**sphinx**](http://sphinx-doc.org/) and **sphinx-rtd-theme**
   - `pip install Sphinx sphinx-rtd-theme`
 - `cd docs`
 - `make html`

**Note!** `make` use script `make_shell_docs.py` that generates `*.rst` files for shell scripts:
 - used for documentation creation (docs/source/scripts/):
   - `genestack-user-setup.rst`
 - shown in track, by link from repository (docs/track_docs/):
     - `genestack-application-manager.rst` 
     - `genestack-shell.rst`
   
  `app-manager_usage.rst` is not included to docs itself, it is used in `make_shell_docs.py` 
