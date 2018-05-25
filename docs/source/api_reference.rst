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

.. autoclass:: genestack_client.Application
        :members:
        :show-inheritance:

.. _DataImporter:

DataImporter
------------

.. autoclass:: genestack_client.DataImporter
        :members:
        :show-inheritance:

.. _FilesUtil:

FilesUtil
---------

.. autoclass:: genestack_client.FilesUtil
        :members:
        :show-inheritance:


.. _ShareUtil:

ShareUtil
----------

.. autoclass:: genestack_client.ShareUtil
        :members:
        :show-inheritance:


FileInitializer
---------------

.. autoclass:: genestack_client.FileInitializer
        :members:
        :show-inheritance:


SudoUtils
---------

.. autoclass:: genestack_client.SudoUtils
        :members:
        :show-inheritance:

.. _TaskLogViewer:

TaskLogViewer
-------------

.. autoclass:: genestack_client.TaskLogViewer
        :members:
        :show-inheritance:

Expression Navigator
--------------------

.. automodule:: genestack_client.expression_navigator
        :members:
        :undoc-members:

DatasetsUtil
------------
.. autoclass:: genestack_client.DatasetsUtil
        :members:
        :undoc-members:

SampleLinker (Beta)
-------------------
.. autoclass:: genestack_client.samples.SampleLinker
        :members:
        :undoc-members:

Command-Line Applications
*************************

CLApplication
-------------

.. autoclass:: genestack_client.CLApplication
        :members:
        :show-inheritance:

.. include:: _cla_reference.rst

Genestack Objects
*****************

Metainfo
--------

.. autoclass:: genestack_client.Metainfo
        :members:
        :show-inheritance:

Metainfo scalar values
----------------------

.. automodule:: genestack_client.metainfo_scalar_values
        :members:
        :undoc-members:

File filters
------------

.. automodule:: genestack_client.file_filters
        :members:

Genome Queries
--------------

.. autoclass:: genestack_client.genome_query.GenomeQuery
        :members:
        :undoc-members:

.. _fileTypes:

File Types
----------

.. autoclass:: genestack_client.file_types.FileTypes
        :members:
        :undoc-members:

.. _permissions:

File Permissions
----------------

.. autoclass:: genestack_client.file_permissions.Permissions
        :members:
        :undoc-members:

Users and Connections
*********************

Connection
----------

.. autoclass:: genestack_client.Connection
        :members:
        :show-inheritance:

settings.User
-------------

.. autoclass:: genestack_client.settings.User
        :members:
        :show-inheritance:

Helper methods
--------------

get_connection
^^^^^^^^^^^^^^

.. autofunction:: genestack_client.get_connection

make_connection_parser
^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: genestack_client.make_connection_parser


get_user
^^^^^^^^

.. autofunction:: genestack_client.get_user



Exceptions
**********

GenestackException
------------------

.. autoclass:: genestack_client.GenestackException
        :members:
        :show-inheritance:


GenestackServerException
------------------------

.. autoclass:: genestack_client.GenestackServerException
        :members:
        :show-inheritance:


GenestackAuthenticationException
--------------------------------

.. autoclass:: genestack_client.GenestackAuthenticationException
        :members:
        :show-inheritance:


Others
******

GenestackShell
--------------

.. autoclass:: genestack_client.genestack_shell.GenestackShell
        :members:
        :show-inheritance:


Command
-------

.. autoclass:: genestack_client.genestack_shell.Command
        :members:
        :show-inheritance:

SpecialFolders
--------------

.. autoclass:: genestack_client.SpecialFolders
        :members:
        :show-inheritance:
