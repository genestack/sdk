#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import csv

from genestack_client import (FilesUtil, make_connection_parser,
                              get_connection, GenestackException, BioMetainfo)


# keys that have existing dedicated "Genestack" metainfo key names
SPECIAL_KEYS = {'name': BioMetainfo.NAME, 'organism': BioMetainfo.ORGANISM,
                'method': BioMetainfo.METHOD, 'sex': BioMetainfo.SEX,
                'gender': BioMetainfo.SEX, 'age': BioMetainfo.AGE,
                'cell line': BioMetainfo.CELL_LINE, 'accession': BioMetainfo.ACCESSION}


# Logic to parse 'boolean-like' values as metainfo booleans
TRUE_VALUES = {'true', 'yes', 'y'}
FALSE_VALUES = {'false', 'no', 'n'}


def parse_as_boolean(s):
    if s.lower().strip() in TRUE_VALUES:
        return True
    elif s.lower().strip() in FALSE_VALUES:
        return False
    return None


if __name__ == "__main__":
    # parse script arguments
    parser = make_connection_parser()
    parser.add_argument('csv_file', help='Path to the local comma-delimited CSV file containing the data')
    parser.add_argument('local_key', help='Name of the local key to match CSV records and Genestack files names')
    parser.add_argument('folder', help='Accession of the Genestack folder containing the files')

    args = parser.parse_args()
    csv_input = args.csv_file
    local_key = args.local_key

    print "Connecting to Genestack..."

    # get connection and application handlers
    connection = get_connection(args)
    files_util = FilesUtil(connection)

    print "Collecting files..."
    files = files_util.get_file_children(args.folder)
    print "Found %d files. Collecting metadata..." % len(files)
    infos = files_util.get_infos(files)

    identifier_map = {info['name']: info['accession'] for info in infos}

    # parse the CSV file
    with open(csv_input, 'r') as the_file:
        reader = csv.DictReader(the_file, delimiter=",")
        field_names = reader.fieldnames

        if args.local_key not in field_names:
            raise GenestackException("Error: the local key %s is not present in the supplied CSV file" % args.local_key)

        for file_data in reader:
            # find the corresponding file
            local_identifier = file_data[local_key]
            remote_file = identifier_map.get(local_identifier)
            if not remote_file:
                print "Warning: no match found for file name '%s'" % local_identifier
                continue

            # prepare a BioMetainfo object
            metainfo = BioMetainfo()
            for key in field_names:
                # key parsing logic
                value = file_data[key]
                if value == "" or value is None:
                    continue
                if key == args.local_key:
                    continue
                if key == "organism":
                    metainfo.add_organism(BioMetainfo.ORGANISM, value)
                else:
                    metainfo_key = SPECIAL_KEYS.get(key.lower(), key)
                    if parse_as_boolean(value) is not None:
                        metainfo.add_boolean(metainfo_key, parse_as_boolean(value))
                    else:
                        metainfo.add_string(metainfo_key, value)

            # edit the metadata on Genestack
            files_util.add_metainfo_values(remote_file, metainfo)
            print "Edited metainfo for '%s' (%s)" % (local_identifier, remote_file)

    print "All done!"
