#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2023 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

from odm_sdk import (DataImporter, FilesUtil,
                              SpecialFolders, get_connection, make_connection_parser)


def main():
    """
    Simple wrapper for uploading reference genome from public domain:  https://www.ensembl.org/index.html

    For the details of FASTA file naming conventions, please see the README at:
    ftp://ftp.ensembl.org/pub/release-91/fasta/homo_sapiens/dna/README
    """

    args = get_args()
    connection = get_connection(args)
    organism = args.species.replace("_", " ")

    # Generate annotation_url if not specified
    if args.annotation_url:
        annotation_url = args.annotation_url
    else:
        annotation_url = f"ftp://ftp.ensembl.org/pub/release-{args.release}/gtf/{args.species.lower()}/" \
                         f"{args.species}.{args.assembly}.{args.release}.gtf.gz"
    # TODO: Use logger in future
    print(f"Reference genome source URL:\n{annotation_url}")

    # Generate name if not specified
    if args.name:
        name = args.name
    else:
        name = f"{organism} reference genome {args.assembly}.{args.release}"

    # TODO: Use logger in future
    print(f"Reference genome name:\n{name}")

    # Create folder in GenestackFS
    fu = FilesUtil(connection)
    parent = fu.get_folder(fu.get_special_folder(SpecialFolders.CREATED),
                           "Data samples", "Reference genome",
                           create=True)

    # Make api-call
    accession = DataImporter(connection).create_reference_genome(
        parent,
        name=name,
        description=name,
        organism=organism,
        assembly=args.assembly,
        release=args.release,
        annotation_url=annotation_url
    )
    files_util = FilesUtil(connection)
    files_util.initialize([accession])


def get_args():

    parser = make_connection_parser()

    parser.add_argument("--name",
                        help="[Optional] Reference genome name to be set in ODM. "
                             "The name will be generated automatically when the parameter is not specified. ")

    parser.add_argument("--annotation-url",
                        help="[Optional] Direct url to a GTF or GFF annotation file. "
                        "The url will be generated automatically when the parameter is not specified, "
                        "e.g. https://ftp.ensembl.org/pub/release-109/gtf/homo_sapiens/Homo_sapiens.GRCh38.109.gtf.gz")

    # Specific group for required args
    group = parser.add_argument_group("required arguments")

    group.add_argument("--assembly", required=True,
                       help="The genome assembly version (excluding the patch number), "
                       "e.g. \"GRCh38\" or \"mm10\"")
    group.add_argument("--release", required=True,
                       help="The release version according to Ensembl, "
                       "e.g. \"109\"")
    group.add_argument("--species", required=True,
                       help="The systematic name of the species with underscores, "
                       "e.g., \"Homo_sapiens\" or \"Mus_musculus\"")

    return parser.parse_args()


if __name__ == "__main__":
    main()
