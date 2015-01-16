Update from old version
=======================

Major changes
-------------

 - Connection mechanism was changes. ``enviroment.py`` was removed, preferred way to get :doc:`connection`
 - All methods was renamed form ``camelCase`` to ``snake_case``
 - ``ShareUtils`` was removed, its functional moved to ``FilesUtils``
 - All script related to import data moved to ``DataImporter``
 - Colorization is not included to core, so it should be removed.

 - Application manager script was renamed from app-manager to genestack-application-manager, no this script installed with setup. Commands `list versions` and `list applications` was replaced by `versions` and `applications`


About any issues please report to Andrey via skype or track (component pythonSDK)
