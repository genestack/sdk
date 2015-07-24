from genestack import Application, FilesUtil, Metainfo, GenestackException


class DataFlowEditor(Application):
    APPLICATION_ID = 'genestack/datafloweditor'

    def __init__(self, connection, application_id=None):
        Application.__init__(self, connection, application_id)
        self.__cache = {}

    def create_dataflow(self, accession, name=None):
        response = self.invoke('initializeApplicationState', 'createFromSources', accession)

        if response['type'] == 'newPage':
            accession = response['fileInfo']['accession']
        elif response['type'] == 'existingPages':
            file_info = response['fileInfos'][-1]  # Query return first 100 items (MAX QUERY).
                                                   # If there is more then 100 files it will return not last
            accession = file_info['accession']
        else:
            raise GenestackException("Unknown response type: %s" % response['type'])
        if name:
            FilesUtil(self.connection).replace_metainfo_string_value([accession], Metainfo.NAME, name)
        return accession

    def add_files(self, page_accession, node_accession, files):
        node = self.__get_node_by_accession(page_accession, node_accession)
        self.invoke('addFiles', files, node, page_accession)

    def clear_files(self, page_accession, node_accession):
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
        Return node id by its originalAccessions.
        """
        for node, node_data in self.__get_graph(page_accession)['fullGraph'].items():
            if accession in node_data['userData']['originalAccessions']:
                return node
