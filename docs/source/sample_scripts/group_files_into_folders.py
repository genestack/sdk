#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from genestack_client import FilesUtil, make_connection_parser, get_connection

# parse script arguments
parser = make_connection_parser()
parser.add_argument('folder', help='Accession of the Genestack folder storing the files to group by application.')
parser.add_argument('--move-files', action='store_true',
                    help='If present, the original files will be unlinked from the source folder')
args = parser.parse_args()
source_folder = args.folder
move_files = args.move_files

print "Connecting to Genestack..."

# get connection and application handlers
connection = get_connection(args)
files_util = FilesUtil(connection)

print "Collecting files..."
files = files_util.get_file_children(source_folder)
files_count = len(files)
print "Found %d files to organise. Retrieving infos..." % files_count
infos = files_util.get_infos(files)

output_folder = files_util.create_folder("Organized files", parent=source_folder)
grouping_folders = {}

for i, entry in enumerate(infos, 1):
    accession = entry['accession']
    print "Processing file %d of %d (%s)..." % (i, files_count, accession)

    # use either application name, application ID or "Unknown application" (in this order of preference)
    app_entry = entry.get('application')
    if app_entry:
        application = app_entry.get('name') or app_entry.get('id', "Unknown application")
    else:
        application = "Unknown application"

    # if there is a folder for this group, we add the file to it ;
    # otherwise, we create one, add it to our dictionary of folders and add the file to it
    if application not in grouping_folders:
        new_folder = files_util.create_folder("Files for %s" % application, parent=output_folder)
        grouping_folders[application] = new_folder
    files_util.link_file(accession, grouping_folders[application])
    if move_files:
        files_util.unlink_file(accession, source_folder)

print "All done! Your files can be found inside the folder with accession %s" % output_folder
