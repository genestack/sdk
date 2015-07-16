# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

import time
import sys
from genestack import GenestackException

from Connection import Application

STDERR = 'stderr'
STDOUT = 'stdout'


class TaskLogViewer(Application):
    """
    View file initialization task logs.
    """
    APPLICATION_ID = 'genestack/task-log-viewer'

    WAITING_MESSAGE = 'Waiting for log... '

    def view_log(self, accession, log_type=STDOUT, follow=True):
        """
        View `limit` bytes from `offset` of file's last task initialization logs

        :param accession: file accession
        :param log_type: stdout or stderr
        :param follow: do not stop when end of log reached, wait for more
        :rtype: str
        """
        offset = -1
        limit = 128000

        while True:
            log_chunk = self.invoke('getFileInitializationLog', accession, log_type, offset, limit)
            if not log_chunk:
                raise GenestackException('File %s not found or have no tasks.' % accession)

            if log_chunk['content'] is None and not follow:
                break
            elif log_chunk['content'] is None and log_chunk['isTerminal']:
                print 'This log is empty (perhaps there was no log produced)'
                break
            elif log_chunk['content'] is None and not log_chunk['isTerminal']:
                if follow:
                    time.sleep(0.5)
                else:
                    print 'No log produced yet...'
                    break
            elif log_chunk['content'] is not None:
                sys.stdout.write(log_chunk['content'])
                sys.stdout.flush()
            if log_chunk['isTerminal'] or not follow:
                break
            offset = log_chunk['offset']
