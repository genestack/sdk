#!python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
from argparse import RawTextHelpFormatter
from datetime import datetime
from itertools import groupby
from operator import itemgetter

from genestack_client import (DataImporter, FilesUtil, GenestackServerException,
                              GenestackVersionException, SpecialFolders, get_connection,
                              make_connection_parser)

DESCRIPTION = '''Upload raw files to server and try to auto recognize them as genestack files.

- Collecting files:
  Application can handle files and folder (will recursively collect all files).
  All paths must be valid. There is not limit to number of files.

- Uploading:
  Files are stored in subfolder of 'Raw uploads'; subfolder name corresponds
  to user local time. Files are uploaded one by one, each in multiple threads.
  In case of network errors application attempts to retry until number of retries
  exceeded (5 by default), in which case application exits with error code.
  Uploaded data is not lost though and you can continue uploading this file
  from the point you stop.

  ATTENTION: When you upload multiple files from the command line,
  be sure to remove successfully uploaded files from the arguments when before re-running
  uploader, because otherwise all of them will be uploaded to the server again.

- Recognition:
  Recognition done only if all files were uploaded successfully. It works over all files.
  Files that were not recognized are linked to subfolder 'Unrecognized files'.

  ATTENTION: Recognition of big number of files may cause server timeouts.
  Split uploading with recognition into relatively small iterations to prevent timeout
  failures.
'''

# TODO treat paths as groups for recognition:
#    each folder is separate group
#    all files joined in one group

parser = make_connection_parser()
parser.description = DESCRIPTION
parser.formatter_class = RawTextHelpFormatter
group = parser.add_argument_group("command arguments")
group.add_argument('paths',
                   help='path to files or folders',
                   metavar='<paths>', nargs='+')
group.add_argument('-n', '--no-recognition', help="don't try to recognize files", action='store_true')
group.add_argument('-F', '--folder_name', metavar='<name>',
                   help='name of the upload folder, if name is not specified it will be generated')


def friendly_number(number):
    """
    Produce a human-readable value for file size.
    :param number: bytes.
    :return: human-readable string.
    """
    template = '%.1f%sB'
    powers = ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
    base = 1000
    number = float(number)
    for power in powers[:-1]:
        if number < base:
            return template % (number, power)
        number /= base
    return template % (number, powers[-1])


def get_files(paths):
    """
    Get file list by paths. Throws an exception if the file does not exist.

    :param paths: list of paths, can be files or directories.
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
            total_size += os.path.getsize(path)
            continue
        for base, folders, files in os.walk(path, followlinks=False):
            for f in files:
                file_path = os.path.join(base, f)
                files_list.append(file_path)
                total_size += os.path.getsize(file_path)
            for f in folders:
                folder_path = os.path.join(base, f)
                if os.path.islink(folder_path):
                    sys.stderr.write("WARNING: Symlink %s was skipped!\n" % folder_path)
    return files_list, total_size


def upload_files(connection, files, folder_name):
    importer = DataImporter(connection)
    fu = FilesUtil(connection)
    upload = fu.get_special_folder(SpecialFolders.UPLOADED)
    folder_name = folder_name or datetime.now().strftime('Upload %d.%m.%y %H:%M:%S')
    new_folder = fu.create_folder(folder_name, parent=upload,
                                  description='Files uploaded by genestack-uploader')
    accession_file_map = {}
    for f in files:
        accession = importer.load_raw(f)
        fu.link_file(accession, new_folder)
        fu.unlink_file(accession, upload)
        accession_file_map[accession] = f
    return new_folder, folder_name, accession_file_map


def recognize_files(connection, accession_file_map, new_folder):
    # Files Recognition
    fu = FilesUtil(connection)

    application = connection.application('genestack/upload')
    recognised_files = application.invoke('recognizeGroupsByAccession', accession_file_map.keys())

    recognized_accessions = set()
    for x in recognised_files:
        for sources in x['sourceFileInfos'].values():
            for info in sources:
                recognized_accessions.add(info['accession'])

    created_files = application.invoke('createFiles', recognised_files, [], None)
    groups = sorted(created_files['files'], key=itemgetter('kind'))
    for name, group in groupby(groups, key=itemgetter('kind')):
        print(name)
        # maybe sort by filename before printing a group?
        for f in group:
            print('\t%s / %s' % (f['accession'], f['name']))

    unrecognized_file_infos = set(accession_file_map) - recognized_accessions

    if unrecognized_file_infos:
        print('Unrecognized Raw Files')
        for accession in unrecognized_file_infos:
            print('\t%s / %s' % (accession, accession_file_map[accession].decode('utf-8')))
        # move unrecognized files to new folder
        unrecognized_folder = fu.create_folder("Unrecognized files", parent=new_folder)
        for accession in unrecognized_file_infos:
            fu.link_file(accession, unrecognized_folder)
            fu.unlink_file(accession, new_folder)
        print('Unrecognized files moved to %s / %s' % (unrecognized_folder, 'Unrecognized files'))


def main():
    args = parser.parse_args()
    files, size = get_files(args.paths)
    print('Collected %s files with total size: %s' % (len(files), friendly_number(size)))
    try:
        connection = get_connection(args)
    except GenestackVersionException as e:
        sys.stderr.write(str(e))
        sys.stderr.write('\n')
        exit(13)
    new_folder, folder_name, accessions = upload_files(connection, files, args.folder_name)
    print('%s files were uploaded to %s / %s' % (len(accessions), new_folder, folder_name))
    if args.no_recognition:
        exit(0)
    try:
        recognize_files(connection, accessions, new_folder)
    except GenestackServerException as e:
        sys.stderr.write("Recognition failed: %s\n" % e)
        exit(1)


if __name__ == '__main__':
    main()
