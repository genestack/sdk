# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#
from Connection import Application

CALCULATE_CHECKSUMS = 'markKeyForCountChecksum'


class CLApplication(Application):
    APPLICATION_ID = None

    def __repr__(self):
        return self.APPLICATION_ID

    def create_file(self, source_files, name=None, params=None, calculate_checksums=False, expected_checksums=None,
                    initialize=False):
        app_file = self.__create_file(source_files, params)

        if name:
            self.rename_file(app_file, name)

        if calculate_checksums:
            self.connection.application('genestack/bio-test-preprocess').invoke(
                '%s' % CALCULATE_CHECKSUMS, app_file
            )

        if expected_checksums:
            self.connection.application('genestack/bio-test-preprocess').invoke(
                'addCheckSums', app_file, expected_checksums or []
            )

        if initialize:
            self.start(app_file)
        return app_file

    def __create_file(self, source_files, params=None):
        """
            createFile(str, list<str>=None, boolean=False) -> str
            createFile(list<str>, list<str>=None, boolean=False) -> str
            createFile(str, str=None, boolean=False) -> str
            createFile(list<str>, str=None, boolean=False) -> str

            Creates application native file and returns its accession.
            The first argument (source_files) is source file accession(s).
            The second argument (params) is command arguments to be set,
            if None then arguments stay default.
            The third argument (initialize) indicates
            that 'start' method should be called immediately.

            If source file is not found or is not of source file type,
            the corresponding exceptions are thrown.
        """
        source_file_list = source_files if isinstance(source_files, list) else [source_files]
        result_file = self.invoke('createFile', source_file_list)
        if params is not None:
            self.change_command_line_arguments(result_file, params)
        return result_file

    def change_command_line_arguments(self, accession, params):
        """
            changeCommandLineArguments(str, list<str>=None, boolean=False) -> void
            changeCommandLineArguments(str, str=None, boolean=False) -> void

            Changes command arguments in file metainfo.
            The first argument(accession) is a native file accession.
            The second argument(params) is command arguments to be set.

            If native file is not found or is not of native file type
            or is already initialized,
            the corresponding exceptions are thrown.
        """
        self.invoke('changeCommandLineArguments', accession, params if isinstance(params, list) else [params])

    def start(self, accession):
        """
            start(str) -> void

            Calls application 'start' method.
            The first argument(accession) is a native file accession.

            If native file is not found or is not of native file type,
            the corresponding exceptions are thrown.
        """
        self.invoke('start', accession)

    # TODO move to filesUtils
    def rename_file(self, accession, name):
        """
            renameFile(str, str) -> str

            Renames file and returns iys new name.
            The first argument(accession) is a native file accession.
            The second argument(name) is a new file name.
        """
        return self.invoke('renameFile', accession, name)

    def replace_file_reference(self, accession, key, accession_to_remove, accession_to_add):
        """
            replaceFileReference(str, str, str, str) -> void

            Replaces file reference for the native file.
            The first argument(accession) is a native file accession.
            The second argument is the file reference key.
            If file reference key is null, exception is thrown.
            The third parameter is the accession to remove.
            The third parameter is the accession to add.

            If native file is not found or is not of native file type,
            the corresponding exceptions are thrown.
            If the file specified to accessionToAdd is not found,
            the corresponding exceptions are thrown.
        """
        return self.invoke('replaceFileReference', accession, key, accession_to_remove, accession_to_add)


class TestCLApplication(CLApplication):
    APPLICATION_ID = 'genestack/testcla'


class BsmapApplication(CLApplication):
    APPLICATION_ID = 'genestack/bsmap'


class UnalignedReadsQC(CLApplication):
    APPLICATION_ID = 'genestack/unalignedreads-qc'


class AlignedReadsQC(CLApplication):
    APPLICATION_ID = 'genestack/alignedreads-qc'


class MethratioApplication(CLApplication):
    APPLICATION_ID = 'genestack/methratio'


class HTSeqCountsApplication(CLApplication):
    APPLICATION_ID = 'genestack/htseqCount'


class NormalizationApplication(CLApplication):
    APPLICATION_ID = 'genestack/normalization'


class TophatApplication(CLApplication):
    APPLICATION_ID = 'genestack/tophat'


class VariationCallerApplication(CLApplication):
    APPLICATION_ID = 'genestack/variationCaller'


# Preprocess
## preprocess raw reads
class TrimAdaptorsAndContiminations(CLApplication):
    APPLICATION_ID = 'genestack/fastq-mcf'


class FilterByQuality(CLApplication):
    APPLICATION_ID = 'genestack/qualityFilter'


class TrimToFixedLength(CLApplication):
    APPLICATION_ID = 'genestack/fastx-trimmer'


class SubsampleReads(CLApplication):
    APPLICATION_ID = 'genestack/subsampling'


class FilterDuplicatedReads(CLApplication):
    APPLICATION_ID = 'genestack/filter-duplicated-reads'


class TrimLowQualityBases(CLApplication):
    APPLICATION_ID = 'genestack/trim-low-quality-bases'


## preprocess mapped reads
class MarkDuplicated(CLApplication):
    APPLICATION_ID = 'genestack/markDuplicates'


class RemoveDuplicates(CLApplication):
    APPLICATION_ID = 'genestack/removeDuplicates'
