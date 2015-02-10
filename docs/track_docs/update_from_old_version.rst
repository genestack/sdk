Changes from genestack-python epoch
===================================


Changes for users
-----------------

- Application manager script was renamed from ``app-manager.py`` to ``genestack-application-manager.py``, now this script installed by setup.

- Application manager commands ``list versions`` and ``list applications`` was replaced by ``versions`` and ``applications``. See https://trac.genestack.com/wiki/DevStuff/ApplicationsManager

- Application manager default user was changed form localhost root to config default user. To use application manager for local installation add argument ``-u root``

- ``-H`` argument in scripts was changed form alias to host to real host.  If you setup your users you will never need to specify it.

- Creditional saved

  Available hosts::

       localhost:8080
       platform.genestack.org
       internal-dev.genestack.com

- environment.py was removed so you need to specify all users you need via ``genestack-user-setup.py``


Changes for coders
------------------

- Connection mechanism was changes. ``enviroment.py`` was removed. It is replaced by genestack-user-setup.py script.
  There is two way to specify you login params on script launch:
    1) via alias form settings ``script.py -u <alias>`` Login host and password will be used form settings. If -u is not specified default user will be used.
    2) via full connection parametrs  ``script.py -u <email> -H host [-p password]`` then system will not use any information from setup.


- All methods was renamed form ``camelCase`` to ``snake_case``

- `ShareUtils` was removed, its method moved to ``FilesUtils``

- All script related to import data moved to ``DataImporter``

- Colorization is not included to core, so it should be removed.


There is two way to fix script:
   - update scripts to new api
   - temporary fix scripts by adding ``sys.path.insert(0, 'genestack-python')``
