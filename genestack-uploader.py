#!python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#
from datetime import datetime
from itertools import groupby
from operator import itemgetter

import os
import sys
from genestack import make_connection_parser, DataImporter, get_connection, FilesUtil, SpecialFolders


parser = make_connection_parser()
group = parser.add_argument_group("command arguments")
group.add_argument('paths',
                   help='path to files or folders',
                   metavar='<paths>', nargs='+')


def friendly_number(number):
    """
    Make human readable value for size.
    :param number: bytes.
    :return: human friendly string.
    """
    template = '%.1f%s'
    powers = ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
    base = 1000
    number = float(number)
    for power in powers[:-1]:
        if number < base:
            return template % (number, power)
        number //= base
    return template % (number, powers[-1])


def get_files(paths):
    """
    Get file list by paths. Throws corresponding exception then path does not exists.

    :param paths: list of paths, may be files or directories.
    :return:
    """
    errors = []
    for path in paths:
        if not os.path.exists(path):
            errors.append(path)
    if errors:
        sys.stderr.write("Error: Path%s was not found: %s\n" % ('s' if len(paths) > 1 else '', ', '.join(paths)))
        exit(1)

    files_list = []
    total_size = 0
    for path in paths:
        if os.path.isfile(path):
            files_list.append(path)
            continue
        for base, _, files in os.walk(path, followlinks=False):
            for f in files:
                file_path = os.path.join(base, f)
                files_list.append(file_path)
                total_size += os.path.getsize(file_path)
    return files_list, total_size


def upload_files(connection):
    importer = DataImporter(connection)
    fu = FilesUtil(connection)
    upload = fu.get_special_folder(SpecialFolders.UPLOADED)
    folder_name = datetime.strftime(datetime.now(), 'Upload %d.%m.%y %H:%M:%S')
    new_folder = fu.create_folder(folder_name, parent=upload,
                                  description='Files uploaded by genestack-uploader')
    accessions = []
    for f in files:
        accession = importer.load_raw(f)
        fu.link_file(accession, new_folder)
        fu.unlink_file(accession, upload)
        accessions.append(accession)
    fi = fu.invoke('getInfos', accessions)
    return new_folder, folder_name, fi


if __name__ == '__main__':
    args = parser.parse_args()
    files, size = get_files(args.paths)
    print 'Collected %s files with total size: %s' % (len(files), friendly_number(size))
    connection = get_connection(args)
    new_folder, folder_name, file_infos = upload_files(connection)
    print 'Files were uploaded to %s / %s' % (new_folder, folder_name)

    # Files Recognition
    application = connection.application('genestack/upload')
    recognised_files = application.invoke('recognizeGroups', file_infos)

    recognized_accessions = set()
    for x in recognised_files:
        for sources in x['sourceFileInfos'].values():
            for source in sources:
                for info in sources:
                    recognized_accessions.add(info['accession'])

    created_files = application.invoke('createFiles', recognised_files)
    groups = sorted(created_files['files'].values(), key=itemgetter('kind'))
    for name, group in groupby(groups, key=itemgetter('kind')):
        print name
        for f in group:
            print '\t%s / %s' % (f['accession'], f['name'])

    unrecognized_file_infos = [info for info in file_infos if info['accession'] not in recognized_accessions]

    if unrecognized_file_infos:

        print 'Unrecognized Raw Files'
        for info in unrecognized_file_infos:
            print '\t%s / %s' % (info['accession'], info['name'])

        # move unrecognized files to new folder
        fu = FilesUtil(connection)
        unrecognized_folder = fu.create_folder("Unrecognized files", parent=new_folder)
        for info in unrecognized_file_infos:
            fu.link_file(info['accession'], unrecognized_folder)
            fu.unlink_file(info['accession'], new_folder)
        print "Unrecognized files moved to %s / %s" % (unrecognized_folder, "Unrecognized files")



