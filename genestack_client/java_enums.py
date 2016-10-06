# -*- coding: utf-8 -*-

from genestack_client import GenestackException


class JavaClassEnum(object):
    _CLASS_NAME = None

    @classmethod
    def get_all_types(cls):
        return {name for name in dir(cls) if not name.startswith("_")}

    @classmethod
    def get_full_name(cls, name, fail_if_not_found=True):
        if name not in cls.get_all_types():
            if fail_if_not_found:
                raise GenestackException("Entry '%s' not found in %s enumeration" % (name, cls.__name__))
            return None
        return "%s.%s" % (cls._CLASS_NAME, name) if cls._CLASS_NAME is not None else name


class CoreFileType(JavaClassEnum):
    _CLASS_NAME = "com.genestack.api.files"

    AUXILIARY_FILE = "IAuxilaryFile"
    FOLDER = "IFolder"
    SEARCH_FOLDER = "ISearchFolder"
    INDEX_FILE = "IIndexFile"

    APPLICATION_PAGE_FILE = "IApplicationPageFile"
    DICTIONARY_FILE = "IDictionaryFile"
    PREFERENCES_FILE = "IPreferencesFile"
    RAW_FILE = "IRawFile"
    REPORT_FILE = "IReportFile"


class BioFileType(JavaClassEnum):
    _CLASS_NAME = "com.genestack.bio.files"

    EXPERIMENT = "IExperiment"
    REFERENCE_GENOME = "IReferenceGenome"
    VARIATION_FILE = "IVariationFile"
    CODON_TABLE = "ICodonTable"
    HT_SEQ_COUNTS = "IHTSeqCounts"
    UNALIGNED_READS = "IUnalignedReads"
    ALIGNED_READS = "IAlignedReads"

    ASSAY = "IAssay"
    SEQUENCING_ASSAY = "ISequencingAssay"
    MICROARRAY_ASSAY = "IMicroarrayAssay"

    DIFFERENTIAL_EXPRESSION_FILE = "IDifferentialExpressionFile"

    GENOME_BED_DATA = "IGenomeBEDData"
    GENOME_WIGGLE_DATA = "IGenomeWiggleData"


class GenestackPermission(JavaClassEnum):
    _CLASS_NAME = "com.genestack.file"

    FILE_ACCESS = "access"
    FILE_READ_CONTENT = "readContent"
    FILE_WRITE = "write"
    FILE_CLONE_DATA = "cloneData"


class SortOrder(JavaClassEnum):

    BY_NAME = "BY_NAME"
    BY_ACCESSION = "BY_ACCESSION"
    BY_LAST_UPDATE = "BY_LAST_UPDATE"
    DEFAULT = "DEFAULT"
