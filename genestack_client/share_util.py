# coding=utf-8
import collections

from genestack_client import Application


class ShareUtil(Application):
    """
    Application that acts as a facade for sharing-related operations.
    """
    APPLICATION_ID = 'genestack/shareutils'

    def share_files_for_view(self, file_accessions, group_accession, destination_folder=None):
        """
        Share files with viewing permissions. Viewing permissions include finding the shared files
        and running tasks that access their content.

        :param file_accessions: accession or an iterable of accessions of files to be shared
        :type file_accessions: str | collections.Iterable[str]
        :param group_accession: accession of the group to share the files with
        :type group_accession: str
        :param destination_folder: accession of the folder to link shared files into. Typically
               this parameter should be used for linking files into group folders, which is
               currently impossible to do using the :meth:`FilesUtil.link_file` method. No links
               will be created if this parameter is equal to `None`.
        :type destination_folder: str
        """
        self.__share_files(
            'shareFilesForViewing', file_accessions, group_accession, destination_folder
        )

    def share_files_for_edit(self, file_accessions, group_accession, destination_folder=None):
        """
        Share files with editing permissions. Editing permissions include viewing permissions and
        also allow modifying metainfo and linking/unlinking files (only applicable to containers
        and datasets).

        :param file_accessions: accession or an iterable of accessions of files to be shared
        :type file_accessions: str | collections.Iterable[str]
        :param group_accession: accession of the group to share the files with
        :type group_accession: str
        :param destination_folder: accession of the folder to link shared files into. Typically
               this parameter should be used for linking files into group folders, which is
               currently impossible to do using the :meth:`FilesUtil.link_file` method. No links
               will be created if this parameter is equal to `None`.
        :type destination_folder: str
        """
        self.__share_files(
            'shareFilesForEditing', file_accessions, group_accession, destination_folder
        )

    def __share_files(self, method_name, file_accessions, group_accession, destination_folder):
        is_iterable = isinstance(file_accessions, collections.Iterable)
        if is_iterable and not isinstance(file_accessions, basestring):
            file_accessions = list(file_accessions)
        else:
            file_accessions = [file_accessions]

        self.invoke(method_name, file_accessions, [group_accession])
        if destination_folder is not None:
            self.invoke('linkFiles', file_accessions, destination_folder, group_accession)

    def get_available_sharing_groups(self):
        """
        Find groups that the current user can share files with, which means that he is either
        a sharing user or an administrator of these groups.

        :return: dictionary in format 'group accession' -> 'group name'
        :rtype: dict
        """
        return self.invoke('getGroupsToShare')
