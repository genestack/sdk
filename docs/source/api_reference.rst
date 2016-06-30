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

Command-Line Applications
*************************

CLApplication
-------------

.. autoclass:: genestack_client.CLApplication
        :members:
        :show-inheritance:

.. include:: _cla_reference.rst

Metainfo Objects
****************

Metainfo
--------

.. autoclass:: genestack_client.Metainfo
        :members:
        :show-inheritance:

        .. autoattribute:: genestack_client.Metainfo.YEAR
        .. autoattribute:: genestack_client.Metainfo.MONTH
        .. autoattribute:: genestack_client.Metainfo.WEEK
        .. autoattribute:: genestack_client.Metainfo.DAY
        .. autoattribute:: genestack_client.Metainfo.HOUR
        .. autoattribute:: genestack_client.Metainfo.MINUTE
        .. autoattribute:: genestack_client.Metainfo.SECOND
        .. autoattribute:: genestack_client.Metainfo.MILLISECOND

BioMetainfo
-----------

.. autoclass:: genestack_client.BioMetainfo
        :members:
        :show-inheritance:


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
