# -*- coding: utf-8 -*-

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

        :param accessions: list of accessions
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


        :param accessions: list of accessions
        :return: list of dictionaries
        :rtype: list
        """
        return self.invoke('loadInfo', accessions)
