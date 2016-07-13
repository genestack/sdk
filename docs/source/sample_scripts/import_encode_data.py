#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# This script parses ENCODE metadata files such as this one:
# https://www.encodeproject.org/metadata/type=Experiment&replicates.library.biosample.donor.organism.scientific_name = Homo + sapiens & files.file_type = fastq & assay_title = RNA - seq / metadata.tsv

import csv

from genestack_client import (DataImporter, BioMetainfo,
                              make_connection_parser, get_connection,
                              Metainfo)

# ENCODE data
FILE_ACCESSION = "File accession"
PAIRED_ACCESSION = "Paired with"

# dictionary: ENCODE file column name -> Genestack metainfo key (None when identical)
VALID_FIELDS = {
    FILE_ACCESSION: Metainfo.NAME,
    "Experiment accession": None,
    "Biosample sex": BioMetainfo.SEX,
    "Biosample organism": BioMetainfo.ORGANISM,
    "Biosample Age": None,
    "Biosample term name": BioMetainfo.CELL_TYPE,
    "Platform": BioMetainfo.PLATFORM
}

ENCODE_URL_PATTERN = "https://www.encodeproject.org/files/{0}/@@download/{0}.fastq.gz"

# parse script arguments
parser = make_connection_parser()
parser.add_argument('tsv_file', metavar='<tsv_file>',
                    help='Path to the local tab-delimited file containing the data')

args = parser.parse_args()
tsv_input = args.tsv_file

print "Connecting to Genestack..."

# get connection and application handlers
connection = get_connection(args)
importer = DataImporter(connection)

# create the experiment where we will store the data in Genestack
experiment = importer.create_experiment(name="ENCODE Human RNA-seq",
                                        description="Human RNA-seq assays from ENCODE")

print "Created a new experiment with accession %s..." % experiment

created_pairs = set()

# parse the CSV file
with open(tsv_input, 'r') as the_file:
    reader = csv.DictReader(the_file, dialect='excel_tab')
    field_names = reader.fieldnames

    for file_data in reader:

        # skip the entry if the file was already included in a previously created paired-end assay
        if file_data[FILE_ACCESSION] in created_pairs:
            continue

        # for each entry, prepare a BioMetainfo object
        metainfo = BioMetainfo()
        for key in VALID_FIELDS.keys():
            metainfo.add_string(VALID_FIELDS.get(key) or key, file_data[key])
        metainfo.add_external_link(BioMetainfo.READS_LINK, ENCODE_URL_PATTERN.format(file_data[FILE_ACCESSION]))

        if file_data.get(PAIRED_ACCESSION):
            # add URL of second mate if the reads are paired-end
            metainfo.add_string(FILE_ACCESSION, PAIRED_ACCESSION)
            metainfo.add_external_link(BioMetainfo.READS_LINK, ENCODE_URL_PATTERN.format(file_data[PAIRED_ACCESSION]))
            created_pairs.add(file_data[PAIRED_ACCESSION])

        # create the sequencing assay on Genestack
        created_file = importer.create_sequencing_assay(experiment, metainfo=metainfo)

        print "Created file '%s' (%s)" % (file_data[FILE_ACCESSION], created_file)

print "All done!"
