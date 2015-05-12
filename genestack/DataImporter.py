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
    """
    Import files to system. If parent is not specified, file created in special folder ``Imported files``

    Required and recommended values can be set by arguments directly or passed inside BioMetainfo object::

       create_bed(name="Bed", link='link')

       # has same effect as:

       metainfo = BioMetainfo()
       metainfo.add_string(BioMetainfo.NAME, 'name)
       metainfo.add_external_link(BioMetainfo.DATA_LINK, text='link name', url=url)
       create_bed(metainfo=metainfo)

    It is prohibited to pass same value both with argument and in metainfo.

    Supported types of urls for external links:

    There is no difference between file and gzipped file for system, both packed and unpacked files will produce same result.
    If protocol is not specified ``file://`` will be used

    * ``file://``:
        - ``test.txt.gz``
        - ``file://test.txt``

    * ``ftp://``
        - ``ftp://server.com/file.txt``

    * ``http://`` ``https://``
        - ``http://server.com/file.txt``

    * ``ascp://``
        - ``ascp://<user>@<server>:file.txt``

    In case of local file ``Raw Upload`` file will be created.
    """
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
        # FIXME: Use only `fileinfo['accession']` after Dotorg is compatible with this change
        try:
            return fileinfo['accession']
        except:
            return fileinfo['Accession']

    def load_raw(self, file_path):
        """
        Load file to genestack storage, return created file accession.

        :param file_path: existing file path
        :type file_path: str
        :return: accession
        :rtype: str
        """
        # FIXME: Use only genestack/upload after Dotorg is compatible with this change
        try:
            return self.connection.application('genestack/upload').upload_chunked_file(file_path)
        except GenestackException:
            return self.connection.application('genestack/rawloader').upload_chunked_file(file_path)

    def create_bed(self, parent=None, name=None, reference_genome=None, url=None, metainfo=None):
        """
        Create bed file.
        name and url are required fields they can be specified by arguments or via metainfo.

        :param parent: accession of parent folder leave empty for ``Imported files``
        :type parent: str
        :param name: name of the file
        :type name: str
        :param reference_genome: accession of reference genome
        :type reference_genome: str
        :param url: url or local path to file
        :type url: str
        :param metainfo: metainfo object
        :type metainfo: BioMetainfo
        :return: file accession
        :rtype: str
        """
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        reference_genome and metainfo.add_file_reference(BioMetainfo.REFERENCE_GENOME, reference_genome)
        url and metainfo.add_external_link(BioMetainfo.DATA_LINK, text=os.path.basename(url), url=url)
        return self.__invoke_loader('genestack/bedLoader', 'importFile', parent, metainfo)

    def create_vcf(self, parent=None, name=None, reference_genome=None, url=None, metainfo=None):
        """
        Create vcf file.
        name and url are required fields they can be specified by arguments or via metainfo.

        :param parent: accession of parent folder leave empty for ``Imported files``
        :type parent: str
        :param name: name of the file
        :type name: str
        :param reference_genome: accession of reference genome
        :type reference_genome: str
        :param url: url or local path to file
        :type url: str
        :param metainfo: metainfo object
        :type metainfo: BioMetainfo
        :return: file accession
        :rtype: str
        """
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        reference_genome and metainfo.add_file_reference(BioMetainfo.REFERENCE_GENOME, reference_genome)
        url and metainfo.add_external_link(BioMetainfo.DATA_LINK, text=os.path.basename(url), url=url)
        return self.__invoke_loader('genestack/variationFileLoader', 'importFile', parent, metainfo)

    def create_wig(self, parent=None, name=None, reference_genome=None, url=None, metainfo=None):
        """
        Create vcf file.
        name and url are required fields they can be specified by arguments or via metainfo.

        :param parent: accession of parent folder leave empty for ``Imported files``
        :type parent: str
        :param name: name of the file
        :type name: str
        :param reference_genome: accession of reference genome
        :type reference_genome: str
        :param url: url or local path to file
        :type url: str
        :param metainfo: metainfo object
        :type metainfo: BioMetainfo
        :return: file accession
        :rtype: str
        """
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        reference_genome and metainfo.add_file_reference(BioMetainfo.REFERENCE_GENOME, reference_genome)
        url and metainfo.add_external_link(BioMetainfo.DATA_LINK, text=os.path.basename(url), url=url)
        return self.__invoke_loader('genestack/wigLoader', 'importFile', parent, metainfo)

    def create_bam(self,
                   parent=None,
                   name=None,
                   bam_link=None,
                   metainfo=None,
                   organism=None,
                   strain=None,
                   reference_genome=None):
        """
        Create aligned read file.

        :param parent: accession of parent folder leave empty for ``Imported files``
        :type parent: str
        :param name: name of the file
        :type name: str
        :param bam_link: link to bam file, index will be created at initialization stage
        :param metainfo: metainfo object
        :type metainfo: BioMetainfo
        :param organism: organism
        :type organism: str
        :param strain: strain
        :type strain:
        :param reference_genome: reference genome accession
        :type reference_genome: str
        :return: file accession
        :rtype: str
        """
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        organism and metainfo.add_organism(BioMetainfo.ORGANISM, organism)
        strain and metainfo.add_string(BioMetainfo.STRAIN, strain)
        reference_genome and metainfo.add_file_reference(BioMetainfo.REFERENCE_GENOME, reference_genome)
        bam_link and metainfo.add_external_link(BioMetainfo.BAM_FILE_LINK, os.path.basename(bam_link), bam_link)
        return self.__invoke_loader('genestack/alignedReadsLoader', 'importFile', parent, metainfo)

    def create_experiment(self, parent=None, name=None, description=None, metainfo=None):
        """
        Create experiment. name is required.

        :param parent: accession of parent folder leave empty for ``Imported files``
        :type parent: str
        :param name: name of the file
        :type name: str
        :param description: experiment description
        :type description: str
        :param metainfo: metainfo object
        :param metainfo: BioMetainfo
        :return: file accession
        :rtype: str
        """
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        description and metainfo.add_string(BioMetainfo.DESCRIPTION, description)
        return self.__invoke_loader('genestack/experimentLoader', 'addExperiment', parent, metainfo)

    def create_microarray_assay(self, parent, name=None, links=None, method=None, organism=None, metainfo=None):
        """
        Create microarray assay in experiment folder. If parent is not experiment exception will be raised.
        name and links are required fields.

        :param parent: accession of parent experiment
        :type parent: str
        :param name: name of the file
        :type name: str
        :param links: list of urls of local file paths
        :type links: list
        :param method: method
        :type method: str
        :param organism: organism
        :type organism: str
        :param metainfo: metainfo object
        :type metainfo: BioMetainfo
        :return: file accession
        :rtype: str
        """
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        organism and metainfo.add_organism(BioMetainfo.ORGANISM, organism)
        method and metainfo.add_string(BioMetainfo.METHOD, method)
        if links:
            for link in links:
                metainfo.add_external_link(BioMetainfo.READS_LINK, os.path.basename(link), link)
        return self.__invoke_loader('genestack/experimentLoader', 'addMicroarrayAssay', parent, metainfo)

    def create_sequencing_assay(self, parent, name=None, links=None, method=None, organism=None, metainfo=None):
        """
        Create sequencing assay in experiment folder. If parent is not experiment exception will be raised.
        name and links are required fields.

        :param parent: accession of parent experiment
        :type parent: str
        :param name: name of the file
        :type name: str
        :param links: list of urls of local file paths
        :type links: list
        :param method: method
        :type method: str
        :param organism: organism
        :type organism: str
        :param metainfo: metainfo object
        :type metainfo: BioMetainfo
        :return: file accession
        :rtype: str
        """
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        organism and metainfo.add_organism(BioMetainfo.ORGANISM, organism)
        method and metainfo.add_string(BioMetainfo.METHOD, method)
        if links:
            for link in links:
                metainfo.add_external_link(BioMetainfo.READS_LINK, os.path.basename(link), link)
        return self.__invoke_loader('genestack/experimentLoader', 'addSequencingAssay', parent, metainfo)

    def create_unaligned_read(self, parent=None, name=None, links=None, method=None, organism=None, metainfo=None):
        """
        Create unaligned read. Unaligned read can be created in folder.
        name and links are required fields.

        :param parent: accession of parent folder leave empty for ``Imported files``
        :type parent: str
        :param name: name of the file
        :type name: str
        :param links: list of urls of local file paths
        :type links: list
        :param method: method
        :type method: str
        :param organism: organism
        :type organism: str
        :param metainfo: metainfo object
        :type metainfo: BioMetainfo
        :return: file accession
        :rtype: str
        """
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        organism and metainfo.add_organism(BioMetainfo.ORGANISM, organism)
        method and metainfo.add_string(BioMetainfo.METHOD, method)
        if links:
            for link in links:
                metainfo.add_external_link(BioMetainfo.READS_LINK, os.path.basename(link), link)
        return self.__invoke_loader('genestack/unalignedReadsLoader', 'importFile', parent, metainfo)

    def create_genome_annotation(self, parent=None, link=None, name=None, organism=None, reference_genome=None,
                                 strain=None, metainfo=None):
        """
        Create genome annotation.
        name and link are required.

        :param parent: accession of parent folder leave empty for ``Imported files``
        :type parent: str
        :param link: link or local path
        :type link: str
        :param name: name of the file
        :type name: str
        :param organism: organism
        :type organism: str
        :param reference_genome: reference genome accession
        :type reference_genome: str
        :param strain: strain
        :type strain: str
        :param metainfo: metainfo object
        :type metainfo: BioMetainfo
        :return: file accession
        :rtype: str
        """
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        organism and metainfo.add_organism(BioMetainfo.ORGANISM, organism)
        strain and metainfo.add_string(BioMetainfo.STRAIN, strain)
        reference_genome and metainfo.add_file_reference(BioMetainfo.REFERENCE_GENOME, reference_genome)
        if link:
            metainfo.add_external_link(BioMetainfo.DATA_LINK, os.path.basename(link), link)
        return self.__invoke_loader('genestack/genome-annotation-loader', 'addGOAnnotationFile', parent, metainfo)

    def create_codon_table(self, parent=None, metainfo=None):
        metainfo = metainfo or BioMetainfo()
        return self.__invoke_loader('genestack/codonTableLoader', 'addCodonTable', parent, metainfo)

    def create_dbnsfp(self, parent=None, link=None, name=None, organism=None, metainfo=None):
        """
        Create dbNSFP file.  name and link are required.

        :param parent: accession of parent folder leave empty for ``Imported files``
        :type parent: str
        :param link: link or local path
        :type link: str
        :param name: name of the file
        :type name: str
        :param organism: organism
        :type organism: str
        :param metainfo: metainfo object
        :type metainfo: BioMetainfo
        :return: file accession
        :rtype: str
        """
        metainfo = metainfo or BioMetainfo()
        metainfo.add_string(BioMetainfo.DATABASE_ID, 'dbNSFP')
        name and metainfo.add_string(BioMetainfo.NAME, name)
        organism and metainfo.add_organism(BioMetainfo.ORGANISM, organism)
        if link:
            metainfo.add_external_link(BioMetainfo.DATA_LINK, os.path.basename(link), link)
        return self.__invoke_loader('genestack/variationDatabaseLoader', 'addDbNSFP', parent, metainfo)

    def create_reference_genome(self,
                                parent=None,
                                name=None,
                                description='',
                                sequence_urls=None,
                                annotation_url=None,
                                organism=None,
                                assembly=None,
                                release=None,
                                strain=None,
                                metainfo=None):
        """
        Create reference genome.

        :param parent: accession of parent folder leave empty for ``Imported files``
        :type parent: str
        :param name: name of the file
        :type name: str
        :param description: experiment description
        :type description: str
        :param sequence_urls: list urls or local path to sequencing files.
        :type sequence_urls: list
        :param annotation_url: url to annotation file
        :type annotation_url: str
        :param organism: organism
        :param organism: str
        :param assembly: assembly
        :type assembly: str
        :param release: release
        :type release: str
        :param strain: strain
        :type strain: str
        :param metainfo: metainfo object
        :type metainfo: BioMetainfo
        :return:
        """
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
        return self.__invoke_loader('genestack/referenceGenomeLoader', 'importFile', parent, metainfo)

    def create_report_file(self, parent=None, name=None, links=None, metainfo=None):
        """
        Create report file. File can be created in folder.
        name and links are required fields.

        :param parent: accession of parent folder leave empty for ``Imported files``
        :type parent: str
        :param name: name of the file
        :type name: str
        :param links: url or list of urls of local file paths
        :type links: list or str
        :param metainfo: metainfo object
        :type metainfo: BioMetainfo
        :return: file accession
        :rtype: str
        """
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        if links:
            links = links if type(links) == list else [links]
            for link in links:
                metainfo.add_external_link(BioMetainfo.DATA_LINK, os.path.basename(link), link)
        return self.__invoke_loader('genestack/reportLoader', 'importFile', parent, metainfo)
