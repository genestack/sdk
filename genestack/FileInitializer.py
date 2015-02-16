# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

from Connection import Application


class FileInitializer(Application):
    APPLICATION_ID = 'genestack/initializer'

    def initialize(self, accessions):
        """
        Start initialization for specified accessions.
        Missed accession and initialization failures skipped.

        :param accessions: list of accessions
        """
        self.invoke('initialize', accessions)

    # TODO replace to getFileInfo
    def load_info(self, accessions):
        """
        Gets the accession or list of accessions
        and returns the list of maps(one map for one accession):
        'accession': (str) file accession
        'name': (str) file name if the file exists
        'status': (str) initialization status

        Status possible values: 'NoSuchFile',
                                'NotApplicable',
                                'NotStarted',
                                'InProgress',
                                'Complete',
                                'Failed'

        :param accessions: list of accessions
        :return list of maps
        """

        return self.invoke('loadInfo', accessions)
