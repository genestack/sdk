Update from old version
=======================

Major changes
-------------

Changes for users
^^^^^^^^^^^^^^^^^^

 - Application manager script was renamed from ``app-manager.py`` to ``genestack-application-manager.py``, now this script installed by setup.
  Commands ``list versions`` and ``list applications`` was replaced by ``versions`` and ``applications``
  See https://trac.genestack.com/wiki/DevStuff/ApplicationsManager
  Default user for application manager was changed form localhost root to config default user. To use appmanager for local installation add ``-u root``

 - ``-H`` argument in scripts was changed form alias to host to real host.  If you setup your users you will never need to specify it.
   Available hosts::

       localhost:8080
       platform.genestack.org
       internal-dev.genestack.com

 - environment.py was removed so you need to specify all users you need via ``genestack-user-setup.py``


Changes for coders
^^^^^^^^^^^^^^^^^^

 - Connection mechanism was changes. ``enviroment.py`` was removed, see Connection section.
 - All methods was renamed form ``camelCase`` to ``snake_case``
 - `ShareUtils` was removed, its method moved to ``FilesUtils``
 - All script related to import data moved to ``DataImporter``
 - Colorization is not included to core, so it should be removed.


There is two way to fix script:
   - fix scripts to new api
   - temporary fix scripts by adding ``sys.path.insert(0, 'genestack-python')``
