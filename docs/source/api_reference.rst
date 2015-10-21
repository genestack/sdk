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


Command-Line Applications
*************************

CLApplication
-------------

.. autoclass:: genestack_client.CLApplication
        :members:


TestCLApplication
-----------------

.. autoclass:: genestack_client.TestCLApplication
        :members:

BsmapApplication
----------------

.. autoclass:: genestack_client.BsmapApplication
        :members:

UnalignedReadsQC
----------------

.. autoclass:: genestack_client.UnalignedReadsQC
        :members:

MethratioApplication
--------------------

.. autoclass:: genestack_client.MethratioApplication
        :members:

HTSeqCountsApplication
----------------------

.. autoclass:: genestack_client.HTSeqCountsApplication
        :members:

NormalizationApplication
------------------------

.. autoclass:: genestack_client.NormalizationApplication
        :members:

TophatApplication
-----------------

.. autoclass:: genestack_client.TophatApplication
        :members:

VariationCallerApplication
--------------------------

.. autoclass:: genestack_client.VariationCallerApplication
        :members:

FilterByQuality
---------------

.. autoclass:: genestack_client.FilterByQuality
        :members:

TrimToFixedLength
-----------------

.. autoclass:: genestack_client.TrimToFixedLength
        :members:

SubsampleReads
--------------

.. autoclass:: genestack_client.SubsampleReads
        :members:

FilterDuplicatedReads
---------------------

.. autoclass:: genestack_client.FilterDuplicatedReads
        :members:

TrimLowQualityBases
-------------------

.. autoclass:: genestack_client.TrimLowQualityBases
        :members:

MarkDuplicated
--------------

.. autoclass:: genestack_client.MarkDuplicated
        :members:



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
