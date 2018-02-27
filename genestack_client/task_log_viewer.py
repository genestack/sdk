# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import time

from genestack_client import Application, GenestackException


class TaskLogViewer(Application):
    """
    A wrapper class for the Task Logs Viewer application. This application allows you to access the initialization
    logs of a file.
    """
    APPLICATION_ID = 'genestack/task-log-viewer'

    STDERR = 'stderr'
    STDOUT = 'stdout'
    MAX_CHUNK_SIZE = 128000

    def view_log(self, accession, log_type=None, follow=True, offset=0):
        sys.stderr.write('Usage of `TaskLogViewer.view_log` deprecated, use `TaskLogViewer.print_log` instead.\n')
        self.print_log(accession, log_type=log_type, follow=follow, offset=offset)

    def print_log(self, accession, log_type=None, follow=True, offset=0):
        """
        Print a file's latest task initialization logs to `stdout`.
        Raises an exception if the file is not found or has no associated initialization task.
        By default the output `stdout` log is shown. You can also view the `stderr` error log.
        ``follow=True`` will wait until initialization is finished.
        Incoming logs will be printed to the console.

        :param accession: file accession
        :param log_type: `stdout` or `stderr`
        :param follow: if enabled, wait and display new lines as they appear (similar to ``tail --follow``)
        :param offset: offset from which to start retrieving the logs. Set to `-1` if you want to start retrieving
          logs from the latest chunk.
        """
        if not log_type:
            log_type = self.STDOUT
        waiting_message_shown = True

        while True:
            log_chunk = self.invoke('getFileInitializationLog', accession, log_type, offset, self.MAX_CHUNK_SIZE)
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
                        print('No logs were produced.')
                    elif follow and not waiting_message_shown:
                        print('No logs produced yet...')
                        waiting_message_shown = True

                if log_chunk['isTerminal'] or not follow:
                    break

                if follow:
                    time.sleep(0.5)

