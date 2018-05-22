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
        :param destination_folder: accession of the folder to link shared files into. This parameter
               is required for linking files into the group folder, because current user might not
               have enough permissions to do that. No links will be created if this parameter is
               `None`.
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
        :param destination_folder: accession of the folder to link shared files into. This parameter
               is required for linking files into the group folder, because current user might not
               have enough permissions to do that. No links will be created if this parameter is
               `None`.
        :type destination_folder: str
        """
        self.__share_files(
            'shareFilesForEditing', file_accessions, group_accession, destination_folder
        )

    def __share_files(self, method_name, file_accessions, group_accession, destination_folder):
        if isinstance(file_accessions, collections.Iterable) and not isinstance(file_accessions, basestring):
            file_accessions = list(file_accessions)
        else:
            file_accessions = [file_accessions]

        self.invoke(method_name, file_accessions, [group_accession])
        if destination_folder is not None:
            self.invoke('linkFiles', file_accessions, destination_folder, group_accession)
