# -*- coding: utf-8 -*-

import sys

from genestack_client import Application, FilesUtil, GenestackException


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
        Create a native Genestack file with the application and return its accession.
        If a source file is not found or is not of the expected type, an exception will be thrown.

        :param source_files: list of source files accessions
        :type source_files: list
        :param name: if a name is provided, the created file will be renamed
        :type name: str
        :param params: custom command-line arguments strings; if None,
            the application defaults will be used.
        :param params: list
        :param calculate_checksums: a flag used in the initialization script
            to compute checksums for the created files
        :type calculate_checksums: bool
        :param expected_checksums: Dict of expected checksums (``{metainfo_key: expected_checksum}``)
        :type expected_checksums: dict
        :param initialize: should initialization be started immediately
            after the file is created?
        :return: accession of created file
        :rtype: str
        """
        app_file = self.__create_file(source_files, params)

        fu = FilesUtil(self.connection)
        if name:
            fu.rename_file(app_file, name)

        if calculate_checksums:
            fu.mark_for_tests(app_file)

        if expected_checksums:
            fu.add_checksums(app_file, expected_checksums)

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
        Change the command-line arguments strings in a file's metainfo.
        ``params`` is a list of command-line strings.
        Note that the syntax of command-line argument strings is application-specific.
        The only way for you to know which command-line strings to provide it is to look at
        the ``Parameters`` metainfo field of a CLA file that has the correct parameters
        specified through the graphical user interface of the application.

        If the file is not found, does not have the right file type
        or is already initialized, an exception will be thrown.

        :param accession: file accession or accession list
        :type accession: str
        :param params: list of commandlines to be set
        :type params: list
        :return: None
        """
        self.invoke('changeCommandLineArguments', self.__to_list(accession), self.__to_list(params))

    def start(self, accession):
        """
        Start file initialization.
        If the file is not found or is not of the right file type, an exception will be thrown.

        :param accession: file accession or accession list
        :type accession: str
        :return: None
        """
        self.invoke('start', self.__to_list(accession))

    def rename_file(self, accession, name):
        sys.stderr.write('Deprecated: use FilesUtil.rename_file instead\n')
        FilesUtil(self.connection).rename_file(accession, name)

    def replace_file_reference(self, accession, key, accession_to_remove, accession_to_add):
        """
        Replace a file reference on the file.

        If the file is not found or is not of the right file type,
        the corresponding exceptions are thrown.
        If ``accession_to_remove`` or ``accession_to_add`` is not found,
        an exception will be thrown.

        :param accession: file accession or accession list
        :param key: key for source files
        :param accession_to_remove: accession to remove
        :param accession_to_add: accession to add
        :return: None
        """
        self.invoke('replaceFileReference', self.__to_list(accession), key, accession_to_remove, accession_to_add)

    def __to_list(self, string_or_list):
        return string_or_list if isinstance(string_or_list, list) else [string_or_list]


class IntersectApplication(CLApplication):
    """
    Parent class for all intersect applications.
    """
    INTERSECT_OTHER_SOURCE_KEY = "genestack.bio:intersect.otherSourceData"

    def create_file(self, source_files, name=None, params=None, calculate_checksums=False,
                    expected_checksums=None, initialize=False):
        """
        Same as the parent method except that intersect applications also need a separate source
        file to intersect with, so it treats the last element of the ``source_files`` array as that
        file.
        """
        if len(source_files) < 2:
            raise GenestackException('Intersect application requires at least two source files')

        main_source_files = source_files[:-1]
        other_source_file = source_files[-1]

        created_file_accession = super(IntersectApplication, self).create_file(
            main_source_files, name, params, calculate_checksums, expected_checksums, initialize
        )
        self.replace_file_reference(
            accession=created_file_accession,
            key=self.INTERSECT_OTHER_SOURCE_KEY,
            accession_to_remove=None,
            accession_to_add=other_source_file
        )
        return created_file_accession


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


class MergeRawReadsApplication(Application):
    APPLICATION_ID = 'genestack/merge-raw-reads'

    def create_merged_reads(self, sources_folder, grouping_key):
        return self.invoke('createFiles', sources_folder, grouping_key)


# preprocess microarrays

class AffymetrixMicroarraysNormalizationApplication(CLApplication):
    APPLICATION_ID = 'genestack/affymetrix-normalization'


class AgilentMicroarraysNormalizationApplication(CLApplication):
    APPLICATION_ID = 'genestack/agilent-normalization'


class L1000MicroarraysNormalizationApplication(CLApplication):
    APPLICATION_ID = 'genestack/l1000-normalization'


class GenePixMicroarraysNormalizationApplication(CLApplication):
    APPLICATION_ID = 'genestack/genepix-normalization'


class InfiniumMicroarraysNormalizationApplication(CLApplication):
    APPLICATION_ID = 'genestack/infinium-methylation-normalization'


# TODO: Deprecated at 0.20.0, will be removed at 0.23.0.
# TODO: We perform renaming in a scope of global 's' -> 'z' refactoring (american style english).
class AffymetrixMicroarraysNormalisationApplication(CLApplication):
    APPLICATION_ID = 'genestack/affymetrix-normalization'

# TODO: Deprecated at 0.20.0, will be removed at 0.23.0.
# TODO: We perform renaming in a scope of global 's' -> 'z' refactoring (american style english).
class AgilentMicroarraysNormalisationApplication(CLApplication):
    APPLICATION_ID = 'genestack/agilent-normalization'


# preprocess mapped reads

class MarkDuplicated(CLApplication):
    APPLICATION_ID = 'genestack/markDuplicates'


class RemoveDuplicated(CLApplication):
    APPLICATION_ID = 'genestack/removeDuplicates'


class MergeMappedReadsApplication(CLApplication):
    APPLICATION_ID = 'genestack/merge-mapped-reads'


class AlignedReadsSubsamplingApplication(CLApplication):
    APPLICATION_ID = 'genestack/aligned-subsampling'


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


class IntersectGenomicFeaturesMapped(IntersectApplication):
    APPLICATION_ID = 'genestack/intersect-bam'


# analyse raw counts


class SingleCellRNASeqAnalysisApplication(CLApplication):
    APPLICATION_ID = 'genestack/rnaseq'


# analyse Differential Expression Statistics

class GOEnrichmentAnalysis(CLApplication):
    APPLICATION_ID = 'genestack/functionalEnrichmentAnalysis'


# analyse variants

class EffectPredictionApplication(CLApplication):
    APPLICATION_ID = 'genestack/snpeff'


class VariantsAssociationAnalysisApplication(CLApplication):
    APPLICATION_ID = 'genestack/variantsAssociationAnalysis'


class IntersectGenomicFeaturesVariants(IntersectApplication):
    APPLICATION_ID = 'genestack/intersect-vcf'


# Analyse microbiome content

class QiimeMicrobiomeAnalysis(CLApplication):
    APPLICATION_ID = 'genestack/qiime-report'


# Explore apps

class UnalignedReadsQC(CLApplication):
    APPLICATION_ID = 'genestack/unalignedreads-qc'


class FastQCApplicaton(CLApplication):
    APPLICATION_ID = 'genestack/fastqc-report'


class AlignedReadsQC(CLApplication):
    APPLICATION_ID = 'genestack/alignedreads-qc'


class TargetedSequencingQC(CLApplication):
    APPLICATION_ID = 'genestack/alignedreads-qc-enrichment'


class ArrayQualityMetricsApplication(CLApplication):
    APPLICATION_ID = 'genestack/arrayqualitymetrics'


class DoseResponseApplication(CLApplication):
    APPLICATION_ID = 'genestack/dose-response'


class SingleCellRNASeqVisualiserApplication(CLApplication):
    APPLICATION_ID = 'genestack/scrvis'
