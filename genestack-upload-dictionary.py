#!python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

import os
from genestack_client import make_connection_parser, get_connection

DESCRIPTION = '''Upload lists of terms to Genestack as dictionaries to use with metainfo.

The expected input format is a text file where each line contains an entry.
Entries longer than 255 characters will be skipped.
Currently, if two entries have the same characters with a different case (e.g. 'Homo sapiens' and 'HOMO SAPIENS'),
the last entry will overwrite the previous one.
Unicode characters are supported.
'''

MAX_CHAR_COUNT = 500000
MAX_KEY_LENGTH = 255


def upload_dictionary(file_path, genestack_file_name, parser_arguments):
    assert os.path.isfile(file_path), "The specified file does not exist"

    print "Connecting to Genestack..."
    connection = get_connection(parser_arguments)
    dictionary_util = Dict

    entries = []
    char_count = 0
    skipped = 0
    file_basename = os.path.basename(file_path).rsplit(".", 1)[0]
    dictionary_file = dictionary_util.invoke('createDictionary', genestack_file_name or file_basename)
    print "Reading file..."
    with open(file_path, "rU") as text_file:
        for i, line in enumerate(text_file, 1):
            line = line.strip('\n')
            if line.strip() == "":
                continue  # skip blank lines
            word_length = len(line)
            if word_length <= MAX_KEY_LENGTH:
                entries.append(line)
                char_count += len(line)
            else:
                skipped += 1
            if char_count > MAX_CHAR_COUNT:
                dictionary_util.invoke('addToDictionary', dictionary_file, entries)
                entries = []
                char_count = 0
                print "%d entries processed..." % i
        dictionary_util.invoke('addToDictionary', dictionary_file, entries)  # add remaining entries
    if skipped > 0:
        print "WARNING: %d entries were skipped because they were too long" % skipped
    print "Done. The dictionary file is %s" % dictionary_file


if __name__ == "__main__":
    parser = make_connection_parser()
    parser.add_argument("file", help='Text file with list of entries')
    parser.add_argument("-n", help='Name of the file to create on Genestack')
    arguments = parser.parse_args()
    file_path = arguments.file
    genestack_file_name = arguments.n
    upload_dictionary(file_path, genestack_file_name, arguments)
