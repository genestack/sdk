#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-


from genestack_client import *


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
nb_files = len(files)
print "Found %d files to organize. Retrieving metainfo..." % nb_files
infos = files_util.get_complete_infos(files)

output_folder = files_util.create_folder("Organized files", parent=source_folder)
grouping_folders = {}

for i, entry in enumerate(infos):
    accession = entry.get('accession')
    print "Processing file %d of %d (%s)..." % (i + 1, nb_files, accession)

    # use either application name, application ID or "Unknown application" (in this order of preference)
    app_entry = entry.get('application')
    application = (app_entry.get('name') or app_entry.get('id')) if app_entry else None
    application = application or "Unknown application"

    # if there is a folder for this group, we add the file to it ;
    # otherwise, we create one, add it to our dictionary of folders and add the file to it
    if application in grouping_folders:
        group_folder = grouping_folders[application]
    else:
        group_folder = files_util.create_folder("Files for %s" % application, parent=output_folder)
        grouping_folders[application] = group_folder
    files_util.link_file(accession, grouping_folders[application])
    if move_files:
        files_util.unlink_file(accession, source_folder)

print "All done! Your files can be found inside the folder with accession %s" % output_folder

