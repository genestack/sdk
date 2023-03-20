#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2023 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

# For details of FASTA file naming conventions, please see the README at:
# ftp://ftp.ensembl.org/pub/release-91/fasta/homo_sapiens/dna/README

from genestack_client import DataImporter, FilesUtil, SpecialFolders, \
    get_connection, FileInitializer

FTP_REPOSITORY = '{prefix}/pub/release-{release}/{datatype}/{species}/'
ENSEMBLE_PREFIX = 'ftp://ftp.ensembl.org'
GTF_FILENAME = '{species}.{assembly}.{release}.gtf.gz'


def annotation_url(assembly, release, species='Homo_sapiens',
                   prefix=ENSEMBLE_PREFIX):
    gtf_repository = FTP_REPOSITORY.format(prefix=prefix, release=release,
                                           species=species.lower(),
                                           datatype='gtf')
    gtf_filename = GTF_FILENAME.format(assembly=assembly, release=release,
                                       species=species)
    return gtf_repository + gtf_filename


def load_ref_genome(name='',
                    assembly='GRCh38',
                    release='109',
                    species='Homo_sapiens'):
    connection = get_connection()
    fu = FilesUtil(connection)
    parent = fu.get_folder(fu.get_special_folder(SpecialFolders.CREATED),
                           'Data samples', 'Reference genome', create=True)

    organism = species.replace('_', ' ')

    if name == '':
        name = f'{organism} reference genome {assembly}.{release}'

    accession = DataImporter(connection).create_reference_genome(
        parent, name=name,
        description=name,
        organism=organism,
        assembly=assembly,
        release=release,
        annotation_url=annotation_url(assembly, release, species),
        sequence_urls=[]
    )
    file_initializer = FileInitializer(connection)
    file_initializer.initialize([accession])
