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
    """
    Base class to interact with CommandLine Applications.
    Application_ID is required you can pass it as init argument or overwrite it in children.
    Source files and params depends on application.

    """
    APPLICATION_ID = None

    def __repr__(self):
        return self.APPLICATION_ID

    def create_file(self, source_files, name=None, params=None, calculate_checksums=False, expected_checksums=None,
                    initialize=False):
        """
        Creates application native file and returns its accession.
        If source file is not found or is not of source file type, the corresponding exceptions are thrown.

        :param source_files: list of source file accessions
        :type source_files: list
        :param name: if name is specified created file will be renamed
        :type name: str
        :param params: is command arguments to be set, if None then arguments stay default.
        :param params: list
        :param calculate_checksums: flag that used in initialization script to count checsums of created files
        :type calculate_checksums: bool
        :param expected_checksums: List of expected checksums in any order
        :type expected_checksums: list
        :param initialize: flag if initialization should be started immediately
        :return: accession of created file
        :rtype: str
        """
        app_file = self.__create_file(source_files, params)

        if name:
            self.rename_file(app_file, name)

        if calculate_checksums:
            # hack to support both master and stable
            try:

                self.connection.application('genestack/bio-test-cla').invoke(
                    '%s' % CALCULATE_CHECKSUMS, app_file
                )
            except:
                # old version
                self.connection.application('genestack/bio-test-preprocess').invoke(
                    '%s' % CALCULATE_CHECKSUMS, app_file
                )

        if expected_checksums:
            # hack to support both master and stable
            try:
                self.connection.application('genestack/bio-test-cla').invoke(
                    'addCheckSums', app_file, expected_checksums or []
                )
            except:
                # old version
                self.connection.application('bio-test-preprocess').invoke(
                    'addCheckSums', app_file, expected_checksums or []
                )

        if initialize:
            self.start(app_file)
        return app_file

    def __create_file(self, source_files, params=None):
        source_file_list = source_files if isinstance(source_files, list) else [source_files]
        result_file = self.invoke('createFile', source_file_list)
        if params is not None:
            self.change_command_line_arguments(result_file, params)
        return result_file

    def change_command_line_arguments(self, accession, params):
        """
        Changes command arguments in file metainfo.
        params is list of commindlines, each commnaline is string with commands separated with spaces.

        If file is not found or is not of file type
        or is already initialized,
        the corresponding exceptions are thrown.

        :param accession: file accession
        :type accession: str
        :param params: list of commandlines to be set
        :type params: list
        :rtype: None
        """
        self.invoke('changeCommandLineArguments', accession, params if isinstance(params, list) else [params])

    def start(self, accession):
        """
        Starts file initialization.
        If native file is not found or is not of native file type, the corresponding exceptions are thrown.

        :param accession: file accession
        :type accession: str
        :rtype: None
        """
        self.invoke('start', accession)

    # TODO move to filesUtils, why we return name?
    def rename_file(self, accession, name):
        """
        Renames file and returns its new name.

        :param accession: file accession
        :type accession: str
        :param name: name
        :type name: str
        :return: new name
        :rtype: str
        """
        # TODO java return name because javascript require it for callback, should we support same interface in python?
        return self.invoke('renameFile', accession, name)

    def replace_file_reference(self, accession, key, accession_to_remove, accession_to_add):
        """
        Replaces file reference for the file.

        If file is not found or is not of native file type,
        the corresponding exceptions are thrown.
        If accession_to_remove or accession_to_add is not found,
        the corresponding exceptions are thrown.

        :param accession: accession of file
        :param key: key for source files
        :param accession_to_remove: accession to remove
        :param accession_to_add: accession to add
        :rtype: None
        """
        self.invoke('replaceFileReference', accession, key, accession_to_remove, accession_to_add)


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
# preprocess raw reads

# TODO remove this class, this old name leaved here for compatibility
class TrimAdaptorsAndContiminations(CLApplication):
    APPLICATION_ID = 'genestack/fastq-mcf'


class TrimAdaptorsAndContaminants(CLApplication):
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


# preprocess mapped reads
class MarkDuplicated(CLApplication):
    APPLICATION_ID = 'genestack/markDuplicates'


class RemoveDuplicates(CLApplication):
    APPLICATION_ID = 'genestack/removeDuplicates'


# analize
class VariationCaller2Application(CLApplication):
    APPLICATION_ID = 'genestack/variationCaller-v2'


# Unsorted
class BowtieApplication(CLApplication):
    APPLICATION_ID = 'genestack/bowtie'


class BsmapApplicationWG(CLApplication):
    APPLICATION_ID = 'genestack/bsmapWG'


class BWAApplication(CLApplication):
    APPLICATION_ID = 'genestack/bwaMapper'


class RemoveDuplicated(CLApplication):
    APPLICATION_ID = 'genestack/removeDuplicates'


class ConcatenateVariantsApplication(CLApplication):
    APPLICATION_ID = 'genestack/concatenate-variants'


class VariationMergerApplication(CLApplication):
    APPLICATION_ID = 'genestack/merge-vcf'


class CuffquantApplication(CLApplication):
    APPLICATION_ID = 'genestack/cuffquant'


class MergeMappedReadsApplication(CLApplication):
    APPLICATION_ID = 'genestack/samtools-merge'


class VariantsAssociationAnalysisApplication(CLApplication):
    APPLICATION_ID = 'genestack/variantsAssociationAnalysis'


