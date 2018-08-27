# -*- coding: utf-8 -*-


class FileTypes(object):

    _JAVA_PKG = "com.genestack.api.files."
    _JAVA_BIO_PKG = "com.genestack.bio.files."

    # Core file types
    FILE = _JAVA_PKG + "IFile"

    DATASET = _JAVA_PKG + "IDataset"

    AUXILIARY_FILE = _JAVA_PKG + "IAuxiliaryFile"
    CONTAINER = _JAVA_PKG + 'IContainerFile'
    FOLDER = _JAVA_PKG + "IFolder"
    SEARCH_FOLDER = _JAVA_PKG + "ISearchFolder"
    INDEX_FILE = _JAVA_PKG + "IIndexFile"

    APPLICATION_PAGE_FILE = _JAVA_PKG + "IApplicationPageFile"
    DICTIONARY_FILE = _JAVA_PKG + "IDictionaryFile"
    PREFERENCES_FILE = _JAVA_PKG + "IPreferencesFile"
    RAW_FILE = _JAVA_PKG + "IRawFile"
    REPORT_FILE = _JAVA_PKG + "IReportFile"
    SAMPLE = _JAVA_PKG + "ISample"

    # Biological file types
    REFERENCE_GENOME = _JAVA_BIO_PKG + "IReferenceGenome"
    VARIATION_FILE = _JAVA_BIO_PKG + "IVariationFile"
    EXTERNAL_DATABASE = _JAVA_BIO_PKG + "IExternalDataBase"

    CODON_TABLE = _JAVA_BIO_PKG + "ICodonTable"
    GENOME_ANNOTATIONS = _JAVA_BIO_PKG + "IGenomeAnnotations"
    HT_SEQ_COUNTS = _JAVA_BIO_PKG + "IHTSeqCounts"
    UNALIGNED_READS = _JAVA_BIO_PKG + "IUnalignedReads"
    MICROARRAY_DATA = _JAVA_BIO_PKG + "IMicroarrayData"
    ALIGNED_READS = _JAVA_BIO_PKG + "IAlignedReads"

    DIFFERENTIAL_EXPRESSION_FILE = _JAVA_BIO_PKG + "differentialExpression.IDifferentialExpressionFile"

    GENOME_BED_DATA = _JAVA_BIO_PKG + "IGenomeBEDData"
    GENOME_WIGGLE_DATA = _JAVA_BIO_PKG + "IGenomeWiggleData"

    FEATURE_LIST = _JAVA_BIO_PKG + "IFeatureList"
    GENE_EXPRESSION_SIGNATURE = _JAVA_BIO_PKG + "IGeneExpressionSignature"
