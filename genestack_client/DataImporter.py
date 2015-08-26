# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

from urllib import quote
from urlparse import urlparse
import os
import sys

from Exceptions import GenestackException
from BioMetainfo import BioMetainfo

ANNOTATION_KEY = 'genestack.url:annotations'
SEQUENCE_KEY = 'genestack.url:sequence'


class DataImporter(object):
    """
    A class used to import files to a Genestack instance.
    If no ``parent`` is not specified, the files are created in the special folder ``Imported files``

    Required and recommended values can be set by arguments directly or passed inside a ``BioMetainfo`` object::

       create_bed(name="Bed", url="some/url")

       # is equivalent to:
       metainfo = BioMetainfo()
       metainfo.add_string(BioMetainfo.NAME, "Bed")
       metainfo.add_external_link(BioMetainfo.DATA_LINK, "some/url", text="link name")
       create_bed(metainfo=metainfo)

    However, **do not** pass the same value both through the arguments and inside a metainfo object.

    Genestack accepts both compressed and uncompressed files.
    If the protocol is not specified, ``file://`` will be used.
    Special characters should be escaped except ``s3://``. Links to Amazon S3 storage should be formatted
    as in `s3cmd <http://s3tools.org/s3cmd>`__.

    Supported protocols:

    * ``file://``:
        - ``test.txt.gz``
        - ``file://test.txt``
        - ``file%20name.gz``

    * ``ftp://``
        - ``ftp://server.com/file.txt``

    * ``http://`` ``https://``
        - ``http://server.com/file.txt``

    * ``ascp://``
        - ``ascp://<user>@<server>:file.txt``

    * ``s3://``
        -  ``s3://bucket/file.gz``
        -  ``s3://bucket/file name.gz``

    If you are uploading a local file, a ``Raw Upload`` intermediary file will be created on the platform.
    """
    def __init__(self, connection):
        self.connection = connection

    def __process_links(self, metainfo):
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
            else:
                for x in external_link_list:
                    if x['url'].startswith('s3://'):
                        x['url'] = 's3://%s' % quote(x['url'][5:])

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
        self.__process_links(metainfo)
        fileinfo = self.connection.application(application).invoke(method, parent, metainfo)
        # FIXME: Use only `fileinfo['accession']` after Dotorg is compatible with this change
        try:
            return fileinfo['accession']
        except:
            return fileinfo['Accession']

    def load_raw(self, file_path):
        """
        Create a Genestack Raw Upload file from a local file, and return the accession of the created file.

        :param file_path: existing file path
        :type file_path: str
        :return: accession
        :rtype: str
        """
        return self.connection.application('genestack/upload').upload_chunked_file(file_path)

    def create_bed(self, parent=None, name=None, reference_genome=None, url=None, metainfo=None):
        """
        Create a Genestack BED Track from a local or remote BED file.
        ``name`` and ``url`` are mandatory fields. They can be specified through the arguments or via a metainfo object.

        :param parent: accession of parent folder. Leave empty for ``Imported files``
        :type parent: str
        :param name: name of the file
        :type name: str
        :param reference_genome: accession of reference genome
        :type reference_genome: str
        :param url: URL or local path to file
        :type url: str
        :param metainfo: metainfo object
        :type metainfo: BioMetainfo
        :return: file accession
        :rtype: str
        """
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        reference_genome and metainfo.add_file_reference(BioMetainfo.REFERENCE_GENOME, reference_genome)
        url and metainfo.add_external_link(BioMetainfo.DATA_LINK, url)
        return self.__invoke_loader('genestack/bedLoader', 'importFile', parent, metainfo)

    def create_vcf(self, parent=None, name=None, reference_genome=None, url=None, metainfo=None):
        """
        Create a Genestack Variants file from a local or remote VCF file.
        ``name`` and ``url`` are required fields. They can be specified through the arguments or via a metainfo object.

        :param parent: accession of parent folder. Leave empty for ``Imported files``
        :type parent: str
        :param name: name of the file
        :type name: str
        :param reference_genome: accession of reference genome
        :type reference_genome: str
        :param url: URL or local path to file
        :type url: str
        :param metainfo: metainfo object
        :type metainfo: BioMetainfo
        :return: file accession
        :rtype: str
        """
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        reference_genome and metainfo.add_file_reference(BioMetainfo.REFERENCE_GENOME, reference_genome)
        url and metainfo.add_external_link(BioMetainfo.DATA_LINK, url)
        return self.__invoke_loader('genestack/variationFileLoader', 'importFile', parent, metainfo)

    def create_wig(self, parent=None, name=None, reference_genome=None, url=None, metainfo=None):
        """
        Create a Genestack Wiggle Track from a local or remote WIG file.
        ``name`` and ``url`` are required fields. They can be specified through the arguments or via a metainfo object.

        :param parent: accession of parent folder. Leave empty for ``Imported files``
        :type parent: str
        :param name: name of the file
        :type name: str
        :param reference_genome: accession of reference genome
        :type reference_genome: str
        :param url: URL or local path to file
        :type url: str
        :param metainfo: metainfo object
        :type metainfo: BioMetainfo
        :return: file accession
        :rtype: str
        """
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        reference_genome and metainfo.add_file_reference(BioMetainfo.REFERENCE_GENOME, reference_genome)
        url and metainfo.add_external_link(BioMetainfo.DATA_LINK, url)
        return self.__invoke_loader('genestack/wigLoader', 'importFile', parent, metainfo)

    def create_bam(self,
                   parent=None,
                   name=None,
                   url=None,
                   metainfo=None,
                   organism=None,
                   strain=None,
                   reference_genome=None):
        """
        Create a Genestack Aligned Reads file from a local or remote BAM file.

        :param parent: accession of parent folder leave empty for ``Imported files``
        :type parent: str
        :param name: name of the file
        :type name: str
        :param url: URL of a BAM file; the index will be created at initialization
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
        url and metainfo.add_external_link(BioMetainfo.BAM_FILE_LINK, url)
        return self.__invoke_loader('genestack/alignedReadsLoader', 'importFile', parent, metainfo)

    def create_experiment(self, parent=None, name=None, description=None, metainfo=None):
        """
        Create a Genestack Experiment. The ``name`` parameter is required.
        It can be specified through the arguments or via a metainfo object.

        :param parent: accession of parent folder. Leave empty for ``Imported files``
        :type parent: str
        :param name: name of the file
        :type name: str
        :param description: experiment description
        :type description: str
        :param metainfo: metainfo object
        :type metainfo: BioMetainfo
        :return: file accession
        :rtype: str
        """
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        description and metainfo.add_string(BioMetainfo.DESCRIPTION, description)
        return self.__invoke_loader('genestack/experimentLoader', 'addExperiment', parent, metainfo)

    def create_microarray_assay(self, parent, name=None, urls=None,
                                method=None, organism=None, metainfo=None):
        """
        Create a Genestack Microarray Assay inside an Experiment folder. If ``parent`` is not an Experiment, an exception will be raised.
        ``name`` and ``urls`` are required fields. They can be specified through the arguments or via a metainfo object.

        :param parent: accession of parent experiment
        :type parent: str
        :param name: name of the file
        :type name: str
        :param urls: list of urls
        :type urls: list
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
        if urls:
            for url in urls:
                metainfo.add_external_link(BioMetainfo.READS_LINK, url)
        return self.__invoke_loader('genestack/experimentLoader', 'addMicroarrayAssay', parent, metainfo)

    def create_sequencing_assay(self, parent, name=None, urls=None,
                                method=None, organism=None, metainfo=None):
        """
        Create a Genestack Sequencing Assay inside an Experiment folder. If ``parent`` is not an Experiment,
        an exception will be raised.
        ``name`` and ``urls`` are required fields. They can be specified through the arguments or via a metainfo object.

        :param parent: accession of the parent experiment
        :type parent: str
        :param name: name of the file
        :type name: str
        :param urls: list of urls
        :type urls: list
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
        if urls:
            for url in urls:
                metainfo.add_external_link(BioMetainfo.READS_LINK, url)
        return self.__invoke_loader('genestack/experimentLoader', 'addSequencingAssay', parent, metainfo)

    def create_unaligned_read(self, parent=None, name=None, urls=None,
                              method=None, organism=None, metainfo=None):
        """
        Create a Genestack Unaligned Reads file from one or several local or remote files. Most common file formats encoding
        sequencing reads with quality scores are accepted (FASTQ 33/64, SRA, FASTA+QUAL, SFF, FAST5).
        ``name`` and ``urls`` are required fields. They can be specified through the arguments or via a metainfo object.

        :param parent: accession of parent folder leave empty for ``Imported files``
        :type parent: str
        :param name: name of the file
        :type name: str
        :param urls: list of urls
        :type urls: list
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
        if urls:
            for url in urls:
                metainfo.add_external_link(BioMetainfo.READS_LINK, url)
        return self.__invoke_loader('genestack/unalignedReadsLoader', 'importFile', parent, metainfo)

    def create_genome_annotation(self, parent=None, url=None, name=None,
                                 organism=None, reference_genome=None,
                                 strain=None, metainfo=None):
        """
        Create a Genestack Genome Annotation file from a local or remote file.
        ``name`` and ``url`` are required fields. They can be specified through the arguments or via a metainfo object.

        :param parent: accession of parent folder. Leave empty for ``Imported files``
        :type parent: str
        :param url: URL or local path
        :type url: str
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
        if url:
            metainfo.add_external_link(BioMetainfo.DATA_LINK, url)
        return self.__invoke_loader('genestack/genome-annotation-loader', 'addGOAnnotationFile', parent, metainfo)

    def create_codon_table(self, parent=None, metainfo=None):
        metainfo = metainfo or BioMetainfo()
        return self.__invoke_loader('genestack/codonTableLoader', 'addCodonTable', parent, metainfo)

    def create_dbnsfp(self, parent=None, url=None, name=None, organism=None, metainfo=None):
        """
        Create a Genestack Variation Database file. ``name`` and ``url`` are required fields.
        They can be specified through the arguments or via a metainfo object.

        :param parent: accession of parent folder leave empty for ``Imported files``
        :type parent: str
        :param url: URL or local path
        :type url: str
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
        if url:
            metainfo.add_external_link(BioMetainfo.DATA_LINK, url)
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
        Create a Genestack Reference Genome from a collection of local or remote FASTA sequence files, and a GTF or GFF
        annotation file.

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
        :type organism: str
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
        annotation_url and metainfo.add_external_link(ANNOTATION_KEY, annotation_url, text='Annotations data link')
        metainfo.add_string(metainfo.DESCRIPTION, description or '')
        for seq_link in sequence_urls:
            metainfo.add_external_link(SEQUENCE_KEY, seq_link, text='Sequence data link')
        return self.__invoke_loader('genestack/referenceGenomeLoader', 'importFile', parent, metainfo)

    def create_report_file(self, parent=None, name=None, urls=None, metainfo=None):
        """
        Create a Genestack Report File from a local or remote data file.
        ``name`` and ``urls`` are required fields.
        They can be specified through the arguments or via a metainfo object.

        :param parent: accession of parent folder leave empty for ``Imported files``
        :type parent: str
        :param name: name of the file
        :type name: str
        :param urls: URL or list of URLs of local file paths
        :type urls: list or str
        :param metainfo: metainfo object
        :type metainfo: BioMetainfo
        :return: file accession
        :rtype: str
        """
        metainfo = metainfo or BioMetainfo()
        name and metainfo.add_string(BioMetainfo.NAME, name)
        if urls:
            for url in urls:
                metainfo.add_external_link(BioMetainfo.DATA_LINK, url)
        return self.__invoke_loader('genestack/reportLoader', 'importFile', parent, metainfo)
