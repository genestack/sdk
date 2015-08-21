# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

from Connection import Application


CALC_CHECKSUMS_METHOD_NAME = 'markKeyForCountChecksum'
ADD_CHECKSUM_METHOD_NAME = 'addCheckSums'


class CLApplication(Application):
    """
    Base class to interact with Genestack command-line applications.
    The ``APPLICATION_ID`` is mandatory. You can either pass it as an argument to the class constructor or override
    it in a child class.
    Source files and parameters are application-specific.

    """
    APPLICATION_ID = None

    def __repr__(self):
        return self.APPLICATION_ID

    def create_file(self, source_files, name=None, params=None, calculate_checksums=False, expected_checksums=None,
                    initialize=False):
        """
        Create a native file with the application and return its accession.
        If a source file is not found or is not of the expected type, an exception will be thrown.

        :param source_files: list of source files accessions
        :type source_files: list
        :param name: if a name is provided, the created file will be renamed
        :type name: str
        :param params: custom command-line arguments strings; if None, the application defaults will be used.
        :param params: list
        :param calculate_checksums: a flag used in the initialization script to compute checksums for the created files
        :type calculate_checksums: bool
        :param expected_checksums: List of expected checksums, in any order
        :type expected_checksums: list
        :param initialize: should initialization be started immediately after the file is created?
        :return: accession of created file
        :rtype: str
        """
        app_file = self.__create_file(source_files, params)

        if name:
            self.rename_file(app_file, name)

        if calculate_checksums:
            self.mark_for_tests(app_file)

        if expected_checksums:
            self.add_checksums(app_file, expected_checksums)

        if initialize:
            self.start(app_file)
        return app_file

    def mark_for_tests(self, app_file):
        """
        Mark file for test via add corresponding key to the metainfo.
        Test file will calculate md5 checksums for processed files stored in the storage during initialization.

        :param app_file: accession of file
        :return: None
        """
        self.connection.application('genestack/bio-test-cla').invoke(
            CALC_CHECKSUMS_METHOD_NAME, app_file)

    def add_checksums(self, app_file, expected_checksums):
        """
        Add expected md5 checksum to the metainfo.
        Expected checksums calculated in the next way:

            - Number of checksums is same as number of entries in the storage. For example Reference Genome have 2 entries (annotation and fasta files).
            - Order of the checksums does not matter (TODO: that might entail problems!).
            - If there are multiple files in one entry it will concatenate them in order as they were PUT to storage by the initialization script.
            - If file marked for test then after initialization metainfo will have both expected and actual checksums.

        :param app_file: accession of application file
        :param expected_checksums: collection of md5 checksums
        :return: None
        """

        self.connection.application('genestack/bio-test-cla').invoke(
            ADD_CHECKSUM_METHOD_NAME, app_file, expected_checksums)

    def __create_file(self, source_files, params=None):
        source_file_list = source_files if isinstance(source_files, list) else [source_files]
        result_file = self.invoke('createFile', source_file_list)
        if params is not None:
            self.change_command_line_arguments(result_file, params)
        return result_file

    def change_command_line_arguments(self, accession, params):
        """
        Change the command-line arguments strings in the file's metainfo.
        ``params`` is a list of command-line strings.

        If the file is not found, does not have the right file type
        or is already initialized, an exception will be thrown.

        :param accession: file accession
        :type accession: str
        :param params: list of commandlines to be set
        :type params: list
        :return: None
        """
        self.invoke('changeCommandLineArguments', accession, params if isinstance(params, list) else [params])

    def start(self, accession):
        """
        Start file initialization.
        If the file is not found or is not of the right file type, an exception will be thrown.

        :param accession: file accession
        :type accession: str
        :return: None
        """
        self.invoke('start', accession)

    # TODO move to filesUtils, why we return name?
    def rename_file(self, accession, name):
        """
        Rename a file and returns its new name.

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
        Replace a file reference on the file.

        If the file is not found or is not of the right file type,
        the corresponding exceptions are thrown.
        If ``accession_to_remove`` or ``accession_to_add`` is not found,
        an exception will be thrown.

        :param accession: accession of file
        :param key: key for source files
        :param accession_to_remove: accession to remove
        :param accession_to_add: accession to add
        :return: None
        """
        self.invoke('replaceFileReference', accession, key, accession_to_remove, accession_to_add)


class TestCLApplication(CLApplication):
    APPLICATION_ID = 'genestack/testcla'


# Preprocess
# preprocess unaligned reads

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


class RemoveDuplicated(CLApplication):
    APPLICATION_ID = 'genestack/removeDuplicates'


class MergeMappedReadsApplication(CLApplication):
    APPLICATION_ID = 'genestack/merge-mapped-reads'


# preprocess variants

class VariationMergerApplication(CLApplication):
    APPLICATION_ID = 'genestack/variationMerger'


class ConcatenateVariantsApplication(CLApplication):
    APPLICATION_ID = 'genestack/concatenateVariants'


# Analise
# analyse unaligned reads

class BowtieApplication(CLApplication):
    APPLICATION_ID = 'genestack/bowtie'


class BsmapApplicationWG(CLApplication):
    APPLICATION_ID = 'genestack/bsmapWG'


class BWAApplication(CLApplication):
    APPLICATION_ID = 'genestack/bwaMapper'


class BsmapApplication(CLApplication):
    APPLICATION_ID = 'genestack/bsmap'


class TophatApplication(CLApplication):
    APPLICATION_ID = 'genestack/tophat'


# analyse mapped reads

class CuffquantApplication(CLApplication):
    APPLICATION_ID = 'genestack/cuffquant'


class MethratioApplication(CLApplication):
    APPLICATION_ID = 'genestack/methratio'


class HTSeqCountsApplication(CLApplication):
    APPLICATION_ID = 'genestack/htseqCount'


class VariationCallerApplication(CLApplication):
    APPLICATION_ID = 'genestack/variationCaller'


class VariationCaller2Application(CLApplication):
    APPLICATION_ID = 'genestack/variationCaller-v2'


class NormalizationApplication(CLApplication):
    APPLICATION_ID = 'genestack/normalization'

class IntersectGenomicFeaturesMapped(CLApplication):
    APPLICATION_ID = 'genestack/intersect-bam'


# analyse variants

class EffectPredictionApplication(CLApplication):
    APPLICATION_ID = 'genestack/snpeff'

class VariantsAssociationAnalysisApplication(CLApplication):
    APPLICATION_ID = 'genestack/variantsAssociationAnalysis'

class IntersectGenomicFeaturesVariants(CLApplication):
    APPLICATION_ID = 'genestack/intersect-vcf'


# Explore apps

class UnalignedReadsQC(CLApplication):
    APPLICATION_ID = 'genestack/unalignedreads-qc'


class FastQCApplicaton(CLApplication):
    APPLICATION_ID = 'genestack/fastqc-report'


class AlignedReadsQC(CLApplication):
    APPLICATION_ID = 'genestack/alignedreads-qc'
