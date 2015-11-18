# Python Client Library

### Documentation

   [stable](http://genestack-client.readthedocs.org/en/stable/)

### Installation
   
   - install library
     - `pip install git+https://github.com/genestack/python-client@stable --upgrade`
   - setup default user
     - `genestack-user-setup init`
   
### Repo

  ```
  docs/                             - folder with documentation sources
  genestack_client/                 - folder with library
  tests/                            - developer tests, require pytest to run.
  genestack-application-manager     - script to connect to application-manager (installed as script)
  genestack-user-setup              - script to setup user (installed as script)
  genestack-uploader                - commandline uploader (installed as script)
  genestack-shell                   - shell (installed as script)
  setup.py                          - installation setup for genestack_client library
  ```

### Generate documentation files

 - install [**sphinx**](http://sphinx-doc.org/) and **sphinx-rtd-theme**
   - `pip install Sphinx sphinx-rtd-theme`
 - `cd docs`
 - `make html`

**Note!** `make` use script `make_shell_docs.py` that generates `*.rst` files for shell scripts:
 - used for documentation creation (docs/source/scripts/):
   - `genestack-user-setup.rst`
 - shown in Trac, by link from repository (docs/track_docs/):
     - `genestack-application-manager.rst` 
     - `genestack-shell.rst`
   
  `app-manager_usage.rst` is not included to docs itself, it is used in `make_shell_docs.py` 
