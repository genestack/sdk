API Reference
#############

This is the complete API reference of the Genestack Client Library. For a more gentle introduction, you can read the :doc:`getting_started` section.

.. toctree::
   :maxdepth: 2

.. _ApplicationWrappers:

Application Wrappers
********************

Application
-----------

.. autoclass:: odm_sdk.Application
        :members:
        :show-inheritance:

.. _DataImporter:

DataImporter
------------

.. autoclass:: odm_sdk.DataImporter
        :members:
        :show-inheritance:

.. _FilesUtil:

FilesUtil
---------

.. autoclass:: odm_sdk.FilesUtil
        :members:
        :show-inheritance:

.. _GroupsUtil:

GroupsUtil
----------

.. autoclass:: odm_sdk.GroupsUtil
        :members:
        :show-inheritance:

.. _ShareUtil:

ShareUtil
---------

.. autoclass:: odm_sdk.ShareUtil
        :members:
        :show-inheritance:

.. _TaskLogViewer:

TaskLogViewer
-------------

.. autoclass:: odm_sdk.TaskLogViewer
        :members:
        :show-inheritance:

Expression Navigator
--------------------

.. automodule:: odm_sdk.expression_navigator
        :members:
        :undoc-members:

DatasetsUtil
------------
.. autoclass:: odm_sdk.DatasetsUtil
        :members:
        :undoc-members:

SampleLinker (Beta)
-------------------
.. autoclass:: odm_sdk.samples.SampleLinker
        :members:
        :undoc-members:

Command-Line Applications
*************************

CLApplication
-------------

.. autoclass:: odm_sdk.CLApplication
        :members:
        :show-inheritance:

.. include:: _cla_reference.rst

Genestack Objects
*****************

Metainfo
--------

.. autoclass:: odm_sdk.Metainfo
        :members:
        :show-inheritance:

Metainfo scalar values
----------------------

.. automodule:: odm_sdk.metainfo_scalar_values
        :members:
        :undoc-members:

File filters
------------

.. automodule:: odm_sdk.file_filters
        :members:

Genome Queries
--------------

.. autoclass:: odm_sdk.genome_query.GenomeQuery
        :members:
        :undoc-members:

.. _fileTypes:

File Types
----------

.. autoclass:: odm_sdk.file_types.FileTypes
        :members:
        :undoc-members:

.. _permissions:

File Permissions
----------------

.. autoclass:: odm_sdk.file_permissions.Permissions
        :members:
        :undoc-members:

Users and Connections
*********************

Connection
----------

.. autoclass:: odm_sdk.Connection
        :members:
        :show-inheritance:

settings.User
-------------

.. autoclass:: odm_sdk.settings.User
        :members:
        :show-inheritance:

Helper methods
--------------

get_connection
^^^^^^^^^^^^^^

.. autofunction:: odm_sdk.get_connection

make_connection_parser
^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: odm_sdk.make_connection_parser


get_user
^^^^^^^^

.. autofunction:: odm_sdk.get_user



Exceptions
**********

GenestackBaseException
----------------------

.. autoclass:: odm_sdk.GenestackBaseException
        :members:
        :show-inheritance:


GenestackException
------------------

.. autoclass:: odm_sdk.GenestackException
        :members:
        :show-inheritance:


GenestackServerException
------------------------

.. autoclass:: odm_sdk.GenestackServerException
        :members:
        :show-inheritance:


GenestackAuthenticationException
--------------------------------

.. autoclass:: odm_sdk.GenestackAuthenticationException
        :members:
        :show-inheritance:


GenestackResponseError
----------------------

.. autoclass:: odm_sdk.GenestackResponseError
        :members:
        :show-inheritance:


GenestackConnectionFailure
--------------------------

.. autoclass:: odm_sdk.GenestackConnectionFailure
        :members:
        :show-inheritance:

Others
******

GenestackShell
--------------

.. autoclass:: odm_sdk.shell.GenestackShell
        :members:
        :show-inheritance:


Command
-------

.. autoclass:: odm_sdk.shell.Command
        :members:
        :show-inheritance:

SpecialFolders
--------------

.. autoclass:: odm_sdk.SpecialFolders
        :members:
        :show-inheritance:
