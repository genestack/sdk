# -*- coding: utf-8 -*-

from genestack_client import Application, FilesUtil, GenestackException, Metainfo


class DataFlowEditor(Application):
    APPLICATION_ID = 'genestack/datafloweditor'

    def __init__(self, connection, application_id=None):
        Application.__init__(self, connection, application_id)
        self.__cache = {}

    def create_dataflow(self, accession, name=None):
        """
        Creates a data flow based on the file provenance of the specified file.
        The nodes of the data flow can be accessed by the accession of the corresponding files in the file provenance.

        :param accession: file accession
        :type accession: str
        :param name: data flow name
        :type name: str
        :return: accession of the created data flow file
        :rtype: str
        :raise GenestackException:
        """
        response = self.invoke('initializeApplicationState', 'createFromSources', accession)

        if response['type'] == 'newPage':
            accession = response['fileInfo']['accession']
        elif response['type'] == 'existingPages':
            # If file already exists we expect to get the last created file.
            # Existing page contains files from first to last (or MAX QUERY)
            # TODO: in case there are more files then MAX QUERY (100 ATM),
            # the last file in response will not be really last
            # (it is almost impossible use case, though)
            file_info = response['fileInfos'][-1]
            accession = file_info['accession']
        else:
            raise GenestackException("Unknown response type: %s" % response['type'])
        if name:
            FilesUtil(self.connection).replace_metainfo_string_value([accession], Metainfo.NAME, name)
        return accession

    def add_files(self, page_accession, node_accession, files):
        """
        Add files to a data flow node.

        :param page_accession: accession of data flow file
        :type page_accession: str
        :param node_accession: accession of origin file in node
        :type node_accession: str
        :param files: list of accessions of files to add to the node
        :type files: list
        :rtype: None
        """
        node = self.__get_node_by_accession(page_accession, node_accession)
        self.invoke('addFiles', files, node, page_accession)

    def clear_node(self, page_accession, node_accession):
        """
        Remove all files from a data flow node.

        :param page_accession: accession of data flow file
        :type page_accession: str
        :param node_accession: accession of origin file in node
        :type node_accession: str
        :rtype: None
        """
        node = self.__get_node_by_accession(page_accession, node_accession)
        self.invoke('clearFile', node, page_accession)

    def __get_graph(self, page_accession):
        """
        Cache graph, to avoid extra requests.
        """
        if page_accession not in self.__cache:
            self.__cache[page_accession] = self.invoke('getFlowData', page_accession)
        return self.__cache[page_accession]

    def __get_node_by_accession(self, page_accession, accession):
        """
        Return node id by its accession.
        """
        for node, node_data in self.__get_graph(page_accession)['fullGraph'].items():
            if accession in node_data['userData']['originalAccessions']:
                return node
