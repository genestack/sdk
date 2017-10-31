# -*- coding: utf-8 -*-

import os
import sys
from urllib import quote
from urlparse import urlparse

from genestack_client import BioMetaKeys, GenestackException, Metainfo
from genestack_client.metainfo_scalar_values import ExternalLink, FileReference, StringValue

ANNOTATION_KEY = 'genestack.url:annotations'
SEQUENCE_KEY = 'genestack.url:sequence'


class DataImporter(object):
    """
    A class used to import files to a Genestack instance.
    If no ``parent`` is specified, the files are created in the special folder ``Imported files``

    Required and recommended values can be set by arguments directly
    or passed inside a :py:class:`~genestack_client.Metainfo`::

       create_bed(name="Bed", url="some/url")

       # is equivalent to:
       metainfo = Metainfo()
       metainfo.add_string(Metainfo.NAME, "Bed")
       metainfo.add_external_link(Metainfo.DATA_LINK, "some/url", text="link name")
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

    #: Affymetrix microarray annotation type
    AFFYMETRIX_ANNOTATION = 'affymetrixMicroarrayAnnotation'
    #: Agilent microarray annotation type
    AGILENT_ANNOTATION = 'agilentMicroarrayAnnotation'
    #: TSV (GenePix etc) microarray annotation type
    TSV_ANNOTATION = 'TSVMicroarrayAnnotation'
    #: Infinium microarray annotation type
    INFINIUM_ANNOTATION = 'methylationArrayAnnotation'

    #: Supported microarray annotation types
    MICROARRAY_ANNOTATION_TYPES = (
        AGILENT_ANNOTATION,
        AFFYMETRIX_ANNOTATION,
        TSV_ANNOTATION,
        INFINIUM_ANNOTATION
    )

    def __init__(self, connection):
        self.connection = connection
        self.importer = connection.application('genestack/upload')

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

    def __invoke_loader(self, parent, importer_type, metainfo):
        self.__process_links(metainfo)
        return self.importer.invoke('createFile', parent, importer_type, metainfo)['accession']

    @staticmethod
    def __add_to_metainfo(metainfo, key, value, value_type, required=False):
        """
        Add ``key``: ``value`` pair to ``metainfo``.

        Fails if:
        * ``metainfo`` already contains ``key``;
        * ``key`` is ``required``, but no value is provided by user,
          and neither ``metainfo`` has already existing ``key`` (with some value).

        :param metainfo: metainfo object to be updated
        :type metainfo: Metainfo
        :param key: key to add
        :type key: str
        :param value: single argument to pass to the value class constructor, or list if need to add many values.
        :type value: object
        :param value_type: value class
        :type value_type: T => genestack_client.metainfo_scalar_values.MetainfoScalarValue
        :param required: flag if value is required
        :type required: bool
        :return: None
        """
        current_value = metainfo.get(key)
        if current_value is not None and value is not None:
            raise GenestackException('Key "%s" is passed both as function argument '
                                     'and inside metainfo object' % key)
        if current_value:
            return

        if required and value is None:
            raise GenestackException('Missing required key "%s", '
                                     'it should be passed as function argument '
                                     'or in metainfo object' % key)
        if value is not None:
            value_list = value if isinstance(value, list) else [value]
            for val in value_list:
                metainfo.add_value(key, value_type(val))

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
        ``name`` and ``url`` are mandatory fields. They can be specified through the arguments or
        via a :py:class:`~genestack_client.Metainfo` instance.

        :param parent: accession of parent folder
            (if not provided, files will be created in the ``Imported files`` folder)
        :type parent: str
        :param name: name of the file
        :type name: str
        :param reference_genome: accession of reference genome
        :type reference_genome: str
        :param url: URL or local path to file
        :type url: str
        :param metainfo: metainfo object
        :type metainfo: Metainfo
        :return: file accession
        :rtype: str
        """
        metainfo = DataImporter._copy_metainfo(metainfo)
        self.__add_to_metainfo(metainfo, Metainfo.NAME, name, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.REFERENCE_GENOME,
                               reference_genome, FileReference)
        self.__add_to_metainfo(metainfo, BioMetaKeys.DATA_LINK, url, ExternalLink, required=True)
        return self.__invoke_loader(parent, 'bedFiles', metainfo)

    def create_vcf(self, parent=None, name=None, reference_genome=None, url=None, metainfo=None):
        """
        Create a Genestack Variants file from a local or remote VCF file.
        ``name`` and ``url`` are required fields. They can be specified through the arguments or
        via a :py:class:`~genestack_client.Metainfo` instance.

        :param parent: accession of parent folder
            (if not provided, files will be created in the ``Imported files`` folder)
        :type parent: str
        :param name: name of the file
        :type name: str
        :param reference_genome: accession of reference genome
        :type reference_genome: str
        :param url: URL or local path to file
        :type url: str
        :param metainfo: metainfo object
        :type metainfo: Metainfo
        :return: file accession
        :rtype: str
        """
        metainfo = DataImporter._copy_metainfo(metainfo)
        self.__add_to_metainfo(metainfo, Metainfo.NAME, name, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.REFERENCE_GENOME,
                               reference_genome, FileReference)
        self.__add_to_metainfo(metainfo, BioMetaKeys.DATA_LINK, url, ExternalLink, required=True)
        return self.__invoke_loader(parent, 'variationFiles', metainfo)

    def create_wig(self, parent=None, name=None, reference_genome=None, url=None, metainfo=None):
        """
        Create a Genestack Wiggle Track from a local or remote WIG file.
        ``name`` and ``url`` are required fields.
        They can be specified through the arguments or
        via a :py:class:`~genestack_client.Metainfo` instance.

        :param parent: accession of parent folder
            (if not provided, files will be created in the ``Imported files`` folder)
        :type parent: str
        :param name: name of the file
        :type name: str
        :param reference_genome: accession of reference genome
        :type reference_genome: str
        :param url: URL or local path to file
        :type url: str
        :param metainfo: metainfo object
        :type metainfo: Metainfo
        :return: file accession
        :rtype: str
        """
        metainfo = DataImporter._copy_metainfo(metainfo)
        self.__add_to_metainfo(metainfo, Metainfo.NAME, name, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.REFERENCE_GENOME,
                               reference_genome, FileReference)
        self.__add_to_metainfo(metainfo, BioMetaKeys.DATA_LINK, url, ExternalLink, required=True)
        return self.__invoke_loader(parent, 'wigFiles', metainfo)

    def create_bam(self,
                   parent=None,
                   name=None,
                   url=None,
                   organism=None,
                   strain=None,
                   reference_genome=None,
                   metainfo=None,
                   ):
        """
        Create a Genestack Aligned Reads file from a local or remote BAM file.
        ``name``, ``url`` and ``organism`` are required fields.
        They can be specified through the arguments or
        via a :py:class:`~genestack_client.Metainfo` instance.


        :param parent: accession of parent folder
            (if not provided, files will be created in the ``Imported files`` folder)
        :type parent: str
        :param name: name of the file
        :type name: str
        :param url: URL of a BAM file; the index will be created at initialization
        :param organism: organism
        :type organism: str
        :param strain: strain
        :type strain:
        :param reference_genome: reference genome accession
        :type reference_genome: str
        :type metainfo: Metainfo
        :param metainfo: metainfo object
        :return: file accession
        :rtype: str
        """
        metainfo = DataImporter._copy_metainfo(metainfo)
        self.__add_to_metainfo(metainfo, Metainfo.NAME, name, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.ORGANISM, organism, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.STRAIN, strain, StringValue)
        self.__add_to_metainfo(metainfo, BioMetaKeys.REFERENCE_GENOME, reference_genome, FileReference)
        self.__add_to_metainfo(metainfo, BioMetaKeys.BAM_FILE_LINK, url, ExternalLink, required=True)
        return self.__invoke_loader(parent, 'alignedReads', metainfo)

    @staticmethod
    def _copy_metainfo(metainfo):
        return Metainfo(metainfo) if metainfo else Metainfo()

    def create_experiment(self, parent=None, name=None, description=None, metainfo=None):
        raise GenestackException('"create_experiment" is not available anymore, '
                                 'use "FilesUtil.create_dataset" method')

    def create_microarray_assay(self, parent, name=None, urls=None,
                                method=None, organism=None, metainfo=None):
        raise GenestackException('"create_microarray_assay" is not available anymore, '
                                 'use "create_microarray_data" method')

    def create_microarray_data(self, parent, name=None, urls=None,
                               method=None, organism=None, metainfo=None):
        """
        Create a Genestack Microarray Data inside an folder.
        ``name`` and ``urls`` are required fields.
        They can be specified through the arguments or
        via a :py:class:`~genestack_client.Metainfo` instance.

        :param parent: accession of parent folder
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
        :type metainfo: Metainfo
        :return: file accession
        :rtype: str
        """
        metainfo = DataImporter._copy_metainfo(metainfo)
        self.__add_to_metainfo(metainfo, Metainfo.NAME, name, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.ORGANISM, organism, StringValue)
        self.__add_to_metainfo(metainfo, BioMetaKeys.METHOD, method, StringValue)
        self.__add_to_metainfo(metainfo, BioMetaKeys.DATA_LINK, urls, ExternalLink, required=True)
        return self.__invoke_loader(parent, 'microarrayData', metainfo)

    def create_infinium_microarray_data(self, parent, name=None, urls=None,
                                        method=None, metainfo=None):
        """
        Create a Genestack Infinium Microarrays Data inside a folder. We can't use create_microarray_data method
        because 'microarrayData' importer can have only one source file, while infinium assay has two. So we invoke
        'infinium MicroarrayData' importer with two links for BioMetaKeys.DATA_LINK key in metainfo.

        Infinum microarrays available only for humans so we have no 'organism' key in arguments.

        :param parent: accession of parent folder
        :type parent: str
        :param name: name of the file
        :type name: str
        :param urls: list of urls
        :type urls: list
        :param method: method
        :type method: str
        :param metainfo: metainfo object
        :type metainfo: Metainfo
        :return: file accession
        :rtype: str
        """
        metainfo = DataImporter._copy_metainfo(metainfo)
        self.__add_to_metainfo(metainfo, Metainfo.NAME, name, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.METHOD, method, StringValue)
        self.__add_to_metainfo(metainfo, BioMetaKeys.DATA_LINK, urls, ExternalLink, required=True)
        return self.__invoke_loader(parent, 'infiniumMicroarrayData', metainfo)

    def create_sequencing_assay(self, parent, name=None, urls=None,
                                method=None, organism=None, metainfo=None):
        raise GenestackException('"create_sequencing_assay" is not available anymore, '
                                 'use "create_unaligned_read" method')

    def create_unaligned_read(self, parent=None, name=None, urls=None,
                              method=None, organism=None, metainfo=None):
        """
        Create a Genestack Unaligned Reads file from one or several local or remote files.
        Most common file formats encoding
        sequencing reads with quality scores are accepted (FASTQ 33/64, SRA, FASTA+QUAL, SFF, FAST5).
        ``name`` and ``urls`` are required fields.
        They can be specified through the arguments or via a :py:class:`~genestack_client.Metainfo` instance.

        :param parent: accession of parent folder
            (if not provided, files will be created in the ``Imported files`` folder)
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
        :type metainfo: Metainfo
        :return: file accession
        :rtype: str
        """
        metainfo = DataImporter._copy_metainfo(metainfo)
        self.__add_to_metainfo(metainfo, Metainfo.NAME, name, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.ORGANISM, organism, StringValue)
        self.__add_to_metainfo(metainfo, BioMetaKeys.METHOD, method, StringValue)
        self.__add_to_metainfo(metainfo, BioMetaKeys.READS_LINK, urls, ExternalLink, required=True)
        return self.__invoke_loader(parent, 'rawReads', metainfo)

    def create_genome_annotation(self, parent=None, url=None, name=None,
                                 organism=None, reference_genome=None,
                                 strain=None, metainfo=None):
        """
        Create a Genestack Genome Annotation file from a local or remote file.
        ``name`` and ``url`` are required fields.
        They can be specified through the arguments or
        via a :py:class:`~genestack_client.Metainfo` instance.

        :param parent: accession of parent folder
            (if not provided, files will be created in the ``Imported files`` folder)
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
        :type metainfo: Metainfo
        :return: file accession
        :rtype: str
        """
        metainfo = DataImporter._copy_metainfo(metainfo)
        self.__add_to_metainfo(metainfo, Metainfo.NAME, name, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.ORGANISM, organism, StringValue)
        self.__add_to_metainfo(metainfo, BioMetaKeys.STRAIN, strain, StringValue)
        self.__add_to_metainfo(metainfo, BioMetaKeys.REFERENCE_GENOME, reference_genome, FileReference)
        self.__add_to_metainfo(metainfo, BioMetaKeys.DATA_LINK, url, ExternalLink, required=True)
        return self.__invoke_loader(parent, 'genomeAnnotations', metainfo)

    def create_codon_table(self, parent=None, metainfo=None):
        metainfo = DataImporter._copy_metainfo(metainfo)
        return self.__invoke_loader(parent, 'codonTables', metainfo)

    def create_dbnsfp(self, parent=None, url=None, name=None, organism=None, metainfo=None):
        """
        Create a Genestack Variation Database file. ``name`` and ``url`` are required fields.
        They can be specified through the arguments or
        via a :py:class:`~genestack_client.Metainfo` instance.

        :param parent: accession of parent folder
            (if not provided, files will be created in the ``Imported files`` folder)
        :type parent: str
        :param url: URL or local path
        :type url: str
        :param name: name of the file
        :type name: str
        :param organism: organism
        :type organism: str
        :param metainfo: metainfo object
        :type metainfo: Metainfo
        :return: file accession
        :rtype: str
        """
        metainfo = DataImporter._copy_metainfo(metainfo)
        metainfo.add_string(BioMetaKeys.DATABASE_ID, 'dbNSFP')
        self.__add_to_metainfo(metainfo, Metainfo.NAME, name, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.ORGANISM, organism, StringValue)
        self.__add_to_metainfo(metainfo, BioMetaKeys.DATA_LINK, url, ExternalLink, required=True)
        return self.__invoke_loader(parent, 'dbnsfp', metainfo)

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
        Create a Genestack Reference Genome from a collection of local or
        remote FASTA sequence files, and a GTF or GFF
        annotation file. ``name``, ``sequence_urls``, ``organism`` and
        ``annotation_url`` are required fields.
        They can be specified through the arguments or
        via a :py:class:`~genestack_client.Metainfo` instance.


        :param parent: accession of parent folder
            (if not provided, files will be created in the ``Imported files`` folder)
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
        :type metainfo: Metainfo
        :return:
        """
        metainfo = DataImporter._copy_metainfo(metainfo)
        self.__add_to_metainfo(metainfo, Metainfo.NAME, name, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.ORGANISM, organism, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.STRAIN, strain, StringValue)
        self.__add_to_metainfo(metainfo, BioMetaKeys.REFERENCE_GENOME_ASSEMBLY, assembly, StringValue)
        self.__add_to_metainfo(metainfo, BioMetaKeys.REFERENCE_GENOME_RELEASE, release, StringValue)
        self.__add_to_metainfo(metainfo, ANNOTATION_KEY, annotation_url, ExternalLink, required=True)
        self.__add_to_metainfo(metainfo, metainfo.DESCRIPTION, description, StringValue)
        self.__add_to_metainfo(metainfo, SEQUENCE_KEY, sequence_urls, ExternalLink)
        return self.__invoke_loader(parent, 'genomes', metainfo)

    def create_report_file(self, parent=None, name=None, urls=None, metainfo=None):
        """
        Create a Genestack Report File from a local or remote data file.
        ``name`` and ``urls`` are required fields.
        They can be specified through the arguments or
        via a :py:class:`~genestack_client.Metainfo` instance.

        :param parent: accession of parent folder
            (if not provided, files will be created in the ``Imported files`` folder)
        :type parent: str
        :param name: name of the file
        :type name: str
        :param urls: URL or list of URLs of local file paths
        :type urls: list or str
        :param metainfo: metainfo object
        :type metainfo: Metainfo
        :return: file accession
        :rtype: str
        """
        metainfo = DataImporter._copy_metainfo(metainfo)
        self.__add_to_metainfo(metainfo, Metainfo.NAME, name, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.DATA_LINK, urls, ExternalLink, required=True)
        return self.__invoke_loader(parent, 'reportFiles', metainfo)

    def create_mapped_reads_count(self,
                                  parent=None,
                                  name=None,
                                  url=None,
                                  reference_genome=None,
                                  metainfo=None):
        """
        Create a Mapped Reads Count file from a local or remote mapped reads count file.
        ``name`` and ``url`` are required fields.
        They can be specified through the arguments or
        via a :py:class:`~genestack_client.Metainfo` instance.

        :param parent: accession of parent folder
            (if not provided, files will be created in the ``Imported files`` folder)
        :type parent: str
        :param name: name of the file
        :type name: str
        :param url: URL of a file
        :param reference_genome: reference genome accession
        :type reference_genome: str
        :param metainfo: metainfo object
        :type metainfo: Metainfo
        :return: file accession
        :rtype: str
        """
        metainfo = DataImporter._copy_metainfo(metainfo)
        self.__add_to_metainfo(metainfo, Metainfo.NAME, name, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.REFERENCE_GENOME, reference_genome, FileReference)
        self.__add_to_metainfo(metainfo, BioMetaKeys.DATA_LINK, url, ExternalLink, required=True)
        return self.__invoke_loader(parent, 'mappedReadCounts', metainfo)

    def create_gene_list(self, parent=None, name=None, url=None,
                         organism=None, metainfo=None):
        """
        Create a Gene List file from a local or remote gene list file.
        ``name``, ``url`` and ``organism`` are required fields.
        They can be specified through the arguments or
        via a :py:class:`~genestack_client.Metainfo` instance.

        :param parent: accession of parent folder
            (if not provided, files will be created in the ``Imported files`` folder)
        :type parent: str
        :param name: name of the file
        :type name: str
        :param url: URL of a file
        :param organism: organism name
        :type organism: str
        :param metainfo: metainfo object
        :type metainfo: Metainfo
        :return: file accession
        :rtype: str
        """
        metainfo = DataImporter._copy_metainfo(metainfo)
        self.__add_to_metainfo(metainfo, Metainfo.NAME, name, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.ORGANISM, organism, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.DATA_LINK, url, ExternalLink, required=True)
        return self.__invoke_loader(parent, 'geneList', metainfo)

    def create_gene_expression_signature(self, parent=None, name=None, url=None,
                                         organism=None, metainfo=None):
        """
        Create a Gene Expression Signature file from a local or remote gene expression signature file.
        ``name``, ``url`` and ``organism`` are required fields.
        They can be specified through the arguments or
        via a :py:class:`~genestack_client.Metainfo` instance.

        :param parent: accession of parent folder
            (if not provided, files will be created in the ``Imported files`` folder)
        :type parent: str
        :param name: name of the file
        :type name: str
        :param url: URL of a file
        :param organism: organism name
        :type organism: str
        :param metainfo: metainfo object
        :type metainfo: Metainfo
        :return: file accession
        :rtype: str
        """
        metainfo = DataImporter._copy_metainfo(metainfo)
        self.__add_to_metainfo(metainfo, Metainfo.NAME, name, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.ORGANISM, organism, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.DATA_LINK, url, ExternalLink, required=True)
        return self.__invoke_loader(parent, 'geneExpressionSignature', metainfo)

    def create_owl_ontology(self, parent=None, name=None, url=None, metainfo=None):
        sys.stderr.write('DataImporter.create_owl_ontology method is deprecated, '
                         'it is renamed to DataImporter.create_dictionary\n')
        return self.create_dictionary(parent=parent, name=name, url=url, metainfo=metainfo)

    def create_dictionary(self, parent=None, name=None, url=None, term_type=None, metainfo=None,
                          parent_dictionary=None):
        """
        Create a Dictionary file from a local or remote file.
        `owl`, `obo`, and `csv` formats are supported.
        ``name`` and ``url`` are required fields.
        They can be specified through the arguments or
        via a :py:class:`~genestack_client.Metainfo` instance.

        :param parent: accession of parent folder
            (if not provided, files will be created in the ``Imported files`` folder)
        :type parent: str
        :param name: name of the file
        :type name: str
        :param url: URL of a file
        :type url: str
        :param term_type: dictionary term type
        :type term_type: str
        :param metainfo: metainfo object
        :type metainfo: Metainfo
        :param parent_dictionary: accession of parent dictionary
        :type parent_dictionary: str
        :return: file accession
        :rtype: str
        """

        metainfo = DataImporter._copy_metainfo(metainfo)
        self.__add_to_metainfo(metainfo, Metainfo.NAME, name, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.DATA_LINK, url, ExternalLink, required=True)
        self.__add_to_metainfo(metainfo, Metainfo.PARENT_DICTIONARY, parent_dictionary, FileReference)
        self.__add_to_metainfo(metainfo, 'genestack.dictionary:termType', term_type, StringValue)
        return self.__invoke_loader(parent, 'dictionaryFiles', metainfo)

    def create_microarray_annotation(self, annotation_type, parent=None,
                                     name=None, url=None, metainfo=None):
        """
        Create a Dictionary file from a local or remote microarray annotation file.
        ``name`` and ``url`` are required fields.
        They can be specified through the arguments or
        via a :py:class:`~genestack_client.Metainfo` instance.

        :param annotation_type: type of annotation being loaded,
            an element of :py:attr:`~genestack_client.DataImporter.MICROARRAY_ANNOTATION_TYPES`
        :type annotation_type: str
        :param parent: accession of parent folder
            (if not provided, files will be created in the ``Imported files`` folder)
        :type parent: str
        :param name: name of the file
        :type name: str
        :param url: URL of a file
        :param metainfo: metainfo object
        :type metainfo: Metainfo
        :return: file accession
        :rtype: str
        """
        if annotation_type not in self.MICROARRAY_ANNOTATION_TYPES:
            raise GenestackException("Microarray annotation type '%s' is not "
                                     "supported, use something from "
                                     "`DataImporter.MICROARRAY_ANNOTATION_TYPES`"
                                     % annotation_type)
        metainfo = DataImporter._copy_metainfo(metainfo)
        self.__add_to_metainfo(metainfo, Metainfo.NAME, name, StringValue, required=True)
        self.__add_to_metainfo(metainfo, BioMetaKeys.DATA_LINK, url, ExternalLink, required=True)
        return self.__invoke_loader(parent, annotation_type, metainfo)
