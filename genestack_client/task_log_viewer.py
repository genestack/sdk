# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2016 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

import time
import sys
from genestack_client import Application, GenestackException


class TaskLogViewer(Application):
    """
    A wrapper class for the Task Logs Viewer application. This application allows you to access the initialization
    logs of a file.
    """
    APPLICATION_ID = 'genestack/task-log-viewer'

    STDERR = 'stderr'
    STDOUT = 'stdout'

    def view_log(self, accession, log_type=None, follow=True):
        """
        Print a file's latest task initialization logs to `stdout`.
        Raises an exception if the file is not found or has no associated initialization task.
        By default the output `stdout` log is shown. You can also view the `stderr` error log.
        ``follow=True`` will wait until initialization is finished.
        Incoming logs will be printed to the console.

        :param accession: file accession
        :param log_type: `stdout` or `stderr`
        :param follow: if enabled, wait and display new lines as they appear (similar to ``tail --follow``)
        """
        if not log_type:
            log_type = self.STDOUT
        offset = 0
        limit = 128000
        waiting_message_shown = True

        while True:
            log_chunk = self.invoke('getFileInitializationLog', accession, log_type, offset, limit)
            if not log_chunk:
                raise GenestackException('File %s not found or has no initialization task' % accession)

            if log_chunk['content'] is not None:
                sys.stdout.write(log_chunk['content'])
                sys.stdout.flush()
                offset += len(log_chunk['content'])
            else:
                # the current chunk is empty
                if offset == 0:
                    if log_chunk['isTerminal']:
                        print "No logs were produced."
                    elif follow and not waiting_message_shown:
                        print "No logs produced yet..."
                        waiting_message_shown = True

                if log_chunk['isTerminal'] or not follow:
                    break

                if follow:
                    time.sleep(0.5)

