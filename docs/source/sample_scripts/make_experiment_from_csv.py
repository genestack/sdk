#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import csv

from genestack_client import (UnalignedReads, DataImporter, BioMetainfo,
                              make_connection_parser, get_connection, GenestackException)

# keys that must be supplied in the CSV file
MANDATORY_KEYS = ['name', 'link']

# keys that have existing dedicated "Genestack" metainfo key names
SPECIAL_KEYS = {'name': BioMetainfo.NAME, 'organism': BioMetainfo.ORGANISM,
                'method': BioMetainfo.METHOD, 'sex': BioMetainfo.SEX,
                'cell line': BioMetainfo.CELL_LINE}

# parse script arguments
parser = make_connection_parser()
parser.add_argument('csv_file', help='Path to the local comma-delimited CSV file containing the data')
parser.add_argument('--name', help='Name of the experiment to create in Genestack')
parser.add_argument('--description', help='Description of the experiment to display in Genestack')

args = parser.parse_args()
csv_input = args.csv_file

print "Connecting to Genestack..."

# get connection and application handlers
connection = get_connection(args)
importer = DataImporter(connection)

# file format of the reads to import
file_format = UnalignedReads.compose_format_map(UnalignedReads.Space.BASESPACE, UnalignedReads.Format.PHRED33,
                                                UnalignedReads.Type.SINGLE)

# create the experiment where we will store the data in Genestack
experiment = importer.create_experiment(name=args.name or "Imported experiment",
                                        description=args.description or "No description provided")

print "Created a new experiment with accession %s..." % experiment


# parse the CSV file
with open(csv_input, 'r') as the_file:
    reader = csv.DictReader(the_file, delimiter=",")
    field_names = reader.fieldnames

    # check if mandatory keys are in the CSV file
    for mandatory_key in MANDATORY_KEYS:
        if mandatory_key not in field_names:
            raise GenestackException("The key '%s' must be supplied in the CSV file. Aborting." % mandatory_key)

    for file_data in reader:

        # for each entry, prepare a BioMetainfo object
        metainfo = BioMetainfo()
        for key in field_names:
            # 'link' and 'organism' are treated separately, as they are added to the metainfo using specific methods
            if key == "link":
                url = file_data[key]
                metainfo.add_external_link(key=BioMetainfo.READS_LINK, text="link", url=url, fmt=file_format)
            elif key == "organism":
                metainfo.add_organism(BioMetainfo.ORGANISM, file_data[key])
            # all the other keys are added as strings
            else:
                metainfo_key = SPECIAL_KEYS.get(key.lower(), key)
                metainfo.add_string(metainfo_key, file_data[key])

        # create the sequencing assay on Genestack
        created_file = importer.create_sequencing_assay(experiment, metainfo=metainfo)

        print "Created file '%s' (%s)" % (file_data['name'], created_file)

print "All done! Bye now..."
