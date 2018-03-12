class GroupsUtil(Application):
    APPLICATION_ID = 'genestack/filesUtil'

    def find_group_by_name(self, name):
        """
        Finds group with specified name.
        If there are no or more than one group with this name, an exception is thrown.

        :param name: group name
        :type name: str
        :return: group accession
        :rtype: str
        """
        return self.invoke(
            'findGroupByName', name
        )
