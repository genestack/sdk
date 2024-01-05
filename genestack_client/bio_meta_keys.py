class BioMetaKeys(object):
    """
    Collection of bio constants.
    """
    METHOD = 'genestack.bio:method'
    ORGANISM = 'genestack.bio:organism'
    STRAIN = 'genestack.bio:strain-breed-cultivar'
    BREED = STRAIN
    CULTIVAR = STRAIN
    TISSUE = 'genestack.bio:tissue'
    CELL_TYPE = 'genestack.bio:cellType'
    CELL_LINE = 'genestack.bio:cellLine'
    DEVELOPMENTAL_STAGE = 'genestack.bio:developmentalStage'
    DISEASE_STATE = 'genestack.bio:disease'
    DISEASE_STAGE = 'genestack.bio:diseaseStage'
    COMPOUND = 'genestack.bio:compoundTreatment/compound'
    COMPOUND_DOSE_VALUE = 'genestack.bio:compoundTreatment/dose/value'
    COMPOUND_DOSE_UNIT = 'genestack.bio:compoundTreatment/dose/unit'
    COMPOUND_TIME_VALUE = 'genestack.bio:compoundTreatment/time/value'
    COMPOUND_TIME_UNIT = 'genestack.bio:compoundTreatment/time/unit'
    AGE = 'genestack.bio:age'
    SEX = 'genestack.bio:sex'
    HUMAN_ETHNIC_GROUP = 'genestack.bio:humanEthnicGroup'
    EXPRESSION_LEVEL_UNIT = 'Expression level unit'
    READS_LINK = 'genestack.url:reads'
    DATA_LINK = 'genestack.url:data'
    BAM_FILE_LINK = 'genestack.url:bamfile'
    REFERENCE_SEQUENCES = 'genestack.bio:referenceSequences'
    REFERENCE_GENOME = 'genestack.bio:referenceGenome'
    REFERENCE_GENOME_ASSEMBLY = 'genestack.bio:referenceGenomeAssembly'
    REFERENCE_GENOME_RELEASE = 'genestack.bio:referenceGenomeRelease'
    STUDY_SHORT_NAME = 'genestack.bio:shortName'
    DATABASE_ID = 'genestack.bio:databaseId'

    RNASEQ_TECHNOLOGY = 'Expression profiling by high throughput sequencing'
    DNASEQ_TECHNOLOGY = 'Genome variation profiling by high throughput sequencing'
    CHIPSEQ_TECHNOLOGY = 'Genome binding/occupancy profiling by high throughput sequencing'
    MICROARRAY_TECHNOLOGY = 'Expression profiling by array'
    DNA_MICROARRAY_TECHNOLOGY = 'Genome variation profiling by SNP array'
    # SAMPLE_ID = 'genestack.bio:sampleId'      # still used in 1000 loader.
    EXTRACTED_MOLECULE = 'genestack.bio:extractedMolecule'
    PLATFORM = 'genestack.bio:platform'
    SOURCE_DATA_PREFIX = 'sourceData:'
    SECONDARY_ACCESSION = 'genestack.bio:secondaryAccession'
