Update from old version
=======================

Major changes
-------------

 - Connection mechanism was changes. ``enviroment.py`` was removed, preferred way to get :doc:`connection`
 - All methods was renamed form ``camelCase`` to ``snake_case``
 - `ShareUtils` was removed, its functional moved to ``FilesUtils``
 - All script related to import data moved to ``DataImporter``
 - Colorization is not included to core, so it should be removed.

 - Application manager script was renamed from ``app-manager.py`` to ``genestack-application-manager.py``, now this script installed by setup.
  Commands ``list versions`` and ``list applications`` was replaced by ``versions`` and ``applications``

There is two way to fix script:
   - fix scripts to new api
   - temporary fix scripts by adding ``sys.path.insert(0, 'genestack-python')``
