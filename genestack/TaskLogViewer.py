# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

import time, sys, itertools

from Connection import Application


class TaskLogViewer(Application):
    """
    View file initialization task logs
    """
    APPLICATION_ID = 'genestack/task-log-viewer'

    def view_log(self, accession, logType="stdout", follow=True):
        """
        View `limit` bytes from `offset` of file's last task initialization logs

        :param accession: file accession
        :param logType: stdout or stderr
        :param follow: do not stop when end of log reached, wait for more
        :rtype: str
        """
        offset = -1
        limit = 128000

        spinner = itertools.cycle(['-', '/', '|', '\\'])

        while True:
            log_chunk = self.invoke('getFileInitializationLog', accession, logType, offset, limit)
            if log_chunk['content'] == None and not follow:
                break
            elif log_chunk['content'] == None and log_chunk['isTerminal']:
                print 'This log is empty (perhaps there was no log produced)'
                break
            elif log_chunk['content'] == None and not log_chunk['isTerminal']:
                if follow:
                    sys.stdout.write('\r')
                    sys.stdout.flush()
                    sys.stdout.write('Waiting for log... ')
                    for _ in range(5):
                        sys.stdout.write(spinner.next())
                        sys.stdout.flush()
                        sys.stdout.write('\b')
                        time.sleep(0.06)
                else:
                    print 'No log produced yet...'
                    break
            elif log_chunk['content'] != None:
                sys.stdout.write('\r')
                sys.stdout.flush()
                sys.stdout.write(log_chunk['content'])
                sys.stdout.flush()
            if log_chunk['isTerminal'] or not follow:
                break
            offset = log_chunk['offset']
