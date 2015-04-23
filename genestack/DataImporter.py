# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

from urlparse import urlparse
import os

from Exceptions import GenestackException
from BioMetainfo import BioMetainfo

ANNOTATION_KEY = 'genestack.url:annotations'
SEQUENCE_KEY = 'genestack.url:sequence'


class DataImporter(object):
    def __init__(self, connection):
        self.connection = connection

    def replace_links_to_raw_files(self, metainfo):
        all_links = [(key, val) for key, val in metainfo.items() if val[0]['type'] == 'externalLink']
        for key, external_link_list in all_links:
            links = [x['url'] for x in external_link_list]
            if self.__are_files_local(links):
                del metainfo[key]
                for external_link in external_link_list:
                    # TODO: fix external_link['format']: set this value after DataFile creation?
                    # Or put it to special metaKey?
                    raw = self.load_raw(external_link['url'])
                    metainfo.add_file_reference(key, raw)

    @staticmethod
    def __are_files_local(links):
        if not isinstance(links, list):
            links = [links]
        if not links:
            return False
        local_flags = set(map(DataImporter.__is_file_local, links))
        if len(local_flags) != 1:
            raise GenestackException('Different types of links: local and remote')
        return local_flags.pop()

    @staticmethod
    def __is_file_local(filepath):
        return DataImporter.__get_local_path(filepath) is not None

    @staticmethod
    def __get_local_path(filepath):
        if os.path.exists(filepath):
            return True
        url_parse = urlparse(filepath)
        # TODO check if next check is have any sense.
        if url_parse.scheme == '' or url_parse.scheme == 'file':
            if not os.path.exists(url_parse.path):
                raise GenestackException('Local file is not found: ' + url_parse.path)
            return url_parse.path
        return None

    def __invoke_loader(self, application, method, parent, metainfo):
        self.replace_links_to_raw_files(metainfo)
        fileinfo = self.connection.application(application).invoke(method, parent, metainfo)
        # TODO: set format for external links?

        # TODO remove after dotorg update.
        # Some dataloaders on dotorg uses old scheme (return string accession)
        # Other uses new scheme (return FileInfo object)
        # This hack allow to use this code both on dotorg and idev
        if isinstance(fileinfo, dict):
            return fileinfo['Accession']
        else:
            return fileinfo

    def load_raw(self, file_path):
        filename = os.path.basename(file_path)
        application = self.connection.application('rawloader-library')
        return application.upload_file(file_path, filename)

    def create_bed(self, parent, name=None, reference_genome=None, url=None, metainfo=None):
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        reference_genome and metainfo.add_file_reference(BioMetainfo.REFERENCE_GENOME, reference_genome)
        url and metainfo.add_external_link(BioMetainfo.DATA_LINK, text=os.path.basename(url), url=url)
        return self.__invoke_loader('bedLoader', 'importFile', parent, metainfo)

    def create_vcf(self, parent, name=None, reference_genome=None, url=None, metainfo=None):
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        reference_genome and metainfo.add_file_reference(BioMetainfo.REFERENCE_GENOME, reference_genome)
        url and metainfo.add_external_link(BioMetainfo.DATA_LINK, text=os.path.basename(url), url=url)
        return self.__invoke_loader('variationFileLoader', 'importFile', parent, metainfo)

    def create_wig(self, parent, name=None, reference_genome=None, url=None, metainfo=None):
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        reference_genome and metainfo.add_file_reference(BioMetainfo.REFERENCE_GENOME, reference_genome)
        url and metainfo.add_external_link(BioMetainfo.DATA_LINK, text=os.path.basename(url), url=url)
        return self.__invoke_loader('wigLoader', 'importFile', parent, metainfo)

    def create_bam(self,
                   parent,
                   name=None,
                   bam_link=None,
                   metainfo=None,
                   organism=None,
                   strain=None,
                   reference_genome=None):
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        organism and metainfo.add_organism(BioMetainfo.ORGANISM, organism)
        strain and metainfo.add_string(BioMetainfo.STRAIN, strain)
        reference_genome and metainfo.add_file_reference(BioMetainfo.REFERENCE_GENOME, reference_genome)
        bam_link and metainfo.add_external_link(BioMetainfo.BAM_FILE_LINK, os.path.basename(bam_link), bam_link)
        return self.__invoke_loader('alignedReadsLoader', 'importFile', parent, metainfo)

    def create_experiment(self, parent, name=None, description=None, metainfo=None):
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        description and metainfo.add_string(BioMetainfo.DESCRIPTION, description)
        return self.__invoke_loader('experimentLoader', 'addExperiment', parent, metainfo)

    def create_microarray_assay(self, parent, name=None, links=None, method=None, organism=None, metainfo=None):
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        organism and metainfo.add_organism(BioMetainfo.ORGANISM, organism)
        method and metainfo.add_string(BioMetainfo.METHOD, method)
        if links:
            for link in links:
                metainfo.add_external_link(BioMetainfo.READS_LINK, os.path.basename(link), link)
        return self.__invoke_loader('experimentLoader', 'addMicroarrayAssay', parent, metainfo)

    def create_sequencing_assay(self, parent, name=None, links=None, method=None, organism=None, metainfo=None):
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        organism and metainfo.add_organism(BioMetainfo.ORGANISM, organism)
        method and metainfo.add_string(BioMetainfo.METHOD, method)
        if links:
            for link in links:
                metainfo.add_external_link(BioMetainfo.READS_LINK, os.path.basename(link), link)
        return self.__invoke_loader('experimentLoader', 'addSequencingAssay', parent, metainfo)

    def create_unaligned_read(self, parent, name=None, links=None, method=None, organism=None, metainfo=None):
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        organism and metainfo.add_organism(BioMetainfo.ORGANISM, organism)
        method and metainfo.add_string(BioMetainfo.METHOD, method)
        if links:
            for link in links:
                metainfo.add_external_link(BioMetainfo.READS_LINK, os.path.basename(link), link)
        return self.__invoke_loader('unalignedReadsLoader', 'importFile', parent, metainfo)

    def create_genome_annotation(self, parent, link=None, name=None, organism=None, reference_genome=None,
                                 strain=None, metainfo=None):
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        organism and metainfo.add_organism(BioMetainfo.ORGANISM, organism)
        strain and metainfo.add_string(BioMetainfo.STRAIN, strain)
        reference_genome and metainfo.add_file_reference(BioMetainfo.REFERENCE_GENOME, reference_genome)
        if link:
            metainfo.add_external_link(BioMetainfo.DATA_LINK, os.path.basename(link), link)
        return self.__invoke_loader('genome-annotation-loader', 'addGOAnnotationFile', parent, metainfo)

    def create_codon_table(self, parent, metainfo=None):
        metainfo = metainfo or BioMetainfo()
        return self.__invoke_loader('codonTableLoader', 'addCodonTable', parent, metainfo)

    def create_dbnsfp(self, parent, link=None, link_text=None, name=None, organism=None, metainfo=None):
        metainfo = metainfo or BioMetainfo()
        metainfo.add_string('genestack.bio:databaseId', 'dbNSFP')
        name and metainfo.add_string(BioMetainfo.NAME, name)
        organism and metainfo.add_organism(BioMetainfo.ORGANISM, organism)
        if link and link_text:
            metainfo.add_external_link(BioMetainfo.DATA_LINK, link_text, link)
        return self.__invoke_loader('variationDatabaseLoader', 'addDbNSFP', parent, metainfo)

    def create_reference_genome(self,
                                parent,
                                name=None,
                                description='',
                                sequence_urls=None,
                                annotation_url=None,
                                organism=None,
                                assembly=None,
                                release=None,
                                strain=None,
                                metainfo=None):
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        organism and metainfo.add_organism(BioMetainfo.ORGANISM, organism)
        strain and metainfo.add_string(BioMetainfo.STRAIN, strain)
        assembly and metainfo.add_string(BioMetainfo.REFERENCE_GENOME_ASSEMBLY, assembly)
        release and metainfo.add_string(BioMetainfo.REFERENCE_GENOME_RELEASE, release)
        annotation_url and metainfo.add_external_link(ANNOTATION_KEY, 'Annotations data link', annotation_url)
        metainfo.add_string(metainfo.DESCRIPTION, description or '')
        for seq_link in sequence_urls:
            metainfo.add_external_link(SEQUENCE_KEY, 'Sequence data link', seq_link)
        return self.__invoke_loader('referenceGenomeLoader', 'importFile', parent, metainfo)
