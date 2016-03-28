# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2016 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

from genestack_client import Metainfo


class BioMetainfo(Metainfo):
    """
    A metainfo representation with additional methods for biological metadata.
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
    AGE = 'genestack.bio:age'
    SEX = 'genestack.bio:sex'
    HUMAN_ETHNIC_GROUP = 'genestack.bio:humanEthnicGroup'
    READS_LINK = 'genestack.url:reads'
    DATA_LINK = 'genestack.url:data'
    BAM_FILE_LINK = 'genestack.url:bamfile'
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

    def add_organism(self, key, value):
        """
        Add an organism value.

        :param key: key
        :type key: str
        :param value: organism name
        :type value: str
        :rtype: None
        """
        self.add_string(key, value)

    def add_ethnic_group(self, key, value):
        """
        Add an ethnic group value.

        :param key: key
        :type key: str
        :param value: ethnic group name
        :type value: str
        :rtype: None
        """
        self.add_string(key, value)
