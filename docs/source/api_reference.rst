API reference
#############


.. toctree::
   :maxdepth: 2


GenestackException
******************

.. autoclass:: genestack_cli.GenestackException
        :members:


GenestackServerException
************************

.. autoclass:: genestack_cli.GenestackServerException
        :members:


Connection
**********

.. autoclass:: genestack_cli.Connection
        :members:

Application
***********

.. autoclass:: genestack_cli.Application
        :members:


Metainfo
********

.. autoclass:: genestack_cli.Metainfo
        :members:
        :show-inheritance:

        .. autoattribute:: genestack_cli.Metainfo.YEAR
        .. autoattribute:: genestack_cli.Metainfo.MONTH
        .. autoattribute:: genestack_cli.Metainfo.WEEK
        .. autoattribute:: genestack_cli.Metainfo.DAY
        .. autoattribute:: genestack_cli.Metainfo.HOUR
        .. autoattribute:: genestack_cli.Metainfo.MINUTE
        .. autoattribute:: genestack_cli.Metainfo.SECOND
        .. autoattribute:: genestack_cli.Metainfo.MILLISECOND

BioMetainfo
***********

.. autoclass:: genestack_cli.BioMetainfo
        :members:
        :show-inheritance:

.. _DataImporter:

DataImporter
************

.. autoclass:: genestack_cli.DataImporter
        :members:

FileInitializer
***************

.. autoclass:: genestack_cli.FileInitializer
        :members:
        :show-inheritance:

.. _FilesUtil:

FilesUtil
*********

.. autoclass:: genestack_cli.FilesUtil
        :members:
        :show-inheritance:


SpecialFolders
**************

.. autoclass:: genestack_cli.SpecialFolders
        :members:

SudoUtils
*********

.. autoclass:: genestack_cli.SudoUtils
        :members:
        :show-inheritance:


CLApplication
*************
.. autoclass:: genestack_cli.CLApplication
        :members:


TestCLApplication
=================

.. autoclass:: genestack_cli.TestCLApplication
        :members:

BsmapApplication
================

.. autoclass:: genestack_cli.BsmapApplication
        :members:

UnalignedReadsQC
================

.. autoclass:: genestack_cli.UnalignedReadsQC
        :members:

MethratioApplication
====================

.. autoclass:: genestack_cli.MethratioApplication
        :members:

HTSeqCountsApplication
======================

.. autoclass:: genestack_cli.HTSeqCountsApplication
        :members:

NormalizationApplication
========================

.. autoclass:: genestack_cli.NormalizationApplication
        :members:

TophatApplication
=================

.. autoclass:: genestack_cli.TophatApplication
        :members:

VariationCallerApplication
==========================

.. autoclass:: genestack_cli.VariationCallerApplication
        :members:

FilterByQuality
===============

.. autoclass:: genestack_cli.FilterByQuality
        :members:

TrimToFixedLength
=================

.. autoclass:: genestack_cli.TrimToFixedLength
        :members:

SubsampleReads
==============

.. autoclass:: genestack_cli.SubsampleReads
        :members:

FilterDuplicatedReads
=====================

.. autoclass:: genestack_cli.FilterDuplicatedReads
        :members:

TrimLowQualityBases
===================

.. autoclass:: genestack_cli.TrimLowQualityBases
        :members:

MarkDuplicated
==============

.. autoclass:: genestack_cli.MarkDuplicated
        :members:

get_connection
**************

.. autofunction:: genestack_cli.get_connection

make_connection_parser
**********************

.. autofunction:: genestack_cli.make_connection_parser

get_user
********

.. autofunction:: genestack_cli.get_user


settings.User
*************

.. autoclass:: genestack_cli.settings.User
        :members:

settings.GenestackShell
***********************

.. autoclass:: genestack_cli.GenestackShell.GenestackShell
        :members:

.. _TaskLogViewer:

TaskLogViewer
*************

.. autoclass:: genestack_cli.TaskLogViewer
        :members:
