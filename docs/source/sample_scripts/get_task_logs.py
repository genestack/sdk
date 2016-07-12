#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from genestack_client import TaskLogViewer, make_connection_parser, get_connection

# add extra arguments to the Genestack arguments parser for this script
parser = make_connection_parser()
parser.add_argument('--follow', action='store_true', help='Follow the logs\' output if the task is not done')
parser.add_argument('--error', action='store_true', help='Display error logs instead of output logs')
parser.add_argument('accession', help='Accession of the file for which to display the logs')
arguments = parser.parse_args()

# connect to Genestack
connection = get_connection(arguments)
log_viewer = TaskLogViewer(connection)

# print task logs
log_type = TaskLogViewer.STDERR if arguments.error else TaskLogViewer.STDOUT
log_viewer.view_log(arguments.accession, log_type=log_type, follow=arguments.follow)
