# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
from genestack_client import Application


class FileInitializer(Application):
    """
    Wrapper class around the File Initializer application.
    """
    APPLICATION_ID = 'genestack/initializer'

    def initialize(self, accessions):
        """
        Start initialization for the specified accessions.
        Missed accession and initialization failures are ignored silently.

        :param list[str] accessions: list of accessions
        :rtype: None
        """
        self.invoke('initialize', accessions)

    # TODO deprecate and use FilesUtil(self.connection).get_infos(accessions) instead
    def load_info(self, accessions):
        """
        Takes as input a list of file accessions and returns a list of dictionaries (one for each accession)
        with the following structure:

            - accession: (str) file accession
            - name: (str) file name if the file exists
            - status: (str) initialization status

        The possible values for ``status`` are:

            - NoSuchFile
            - NotApplicable
            - NotStarted
            - InProgress
            - Complete
            - Failed


        :param list[str] accessions: list of accessions
        :return: list of dictionaries
        :rtype: list
        """
        return self.invoke('loadInfo', accessions)
