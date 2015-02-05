# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

from Exceptions import GenestackException
from Metainfo import Metainfo
from Connection import Application
from SudoUtils import SudoUtils

PRIVATE = 'private'
PUBLIC = 'public'


class SpecialFolders:
    IMPORTED = 'imported'
    CREATED = 'created'
    TEMPORARY = 'temporary'
    UPLOADED = 'uploaded'


class FilesUtil(Application):
    """
    Application for file management.
    """
    APPLICATION_ID = 'filesUtil'

    IFile = 'com.genestack.api.files.IFile'
    IUnalignedReads = 'com.genestack.bio.files.IUnalignedReads'
    IFolder = 'com.genestack.api.files.IFolder'
    IAlignedReads = 'com.genestack.bio.files.IAlignedReads'
    IVariationFile = 'com.genestack.bio.files.IVariationFile'
    IExperiment = 'com.genestack.bio.files.IExperiment'
    IApplicationPageFile = 'com.genestack.files.IApplicationPageFile'
    IContainerFile = 'com.genestack.api.files.IContainerFile'
    IReferenceGenome = 'com.genestack.bio.files.IReferenceGenome'

    def find_reference_genome(self, organism, assembly, release):
        """
        Returns the accession of the reference genome with the specified parameters: organism, assembly, release.
        If more than one or no genome is found, the corresponding exceptions are thrown.

        :param organism: organism
        :type organism: str
        :param assembly: assembly
        :type assembly: str
        :param release: release
        :type release: str
        :return: accession
        :rtype: str
        :raise GenestackServerException:
        """
        return self.invoke('findReferenceGenome', organism, assembly, release)

    def find_file_by_name(self, name, parent=None, file_class=IFile):
        """
        Finds file with specified name (ignore case!) and type.
        If no file is found None is returned.
        If more than one file is found the first one is returned.
        If the parent container is not found, the corresponding exceptions are thrown.

        :param name: file name
        :type name: str
        :param parent: parent accession, private folder is default
        :type parent: str
        :param file_class: File class to be returned, default IFile
        :type file_class: str
        :return: instance of subclass of IFile
        :rtype: IFile
        """
        return self.invoke(
            'getFileByName',
            name, parent, file_class
        )

    # SA: TODO: remove this methods and change usage to findFileByName
    def find_folder_by_name(self, name, parent=None):
        return self.find_file_by_name(name, parent, self.IFolder)

    def find_aligned_reads_file_by_name(self, name, parent=None):
        return self.find_file_by_name(name, parent, self.IAlignedReads)

    def find_unaligned_reads_file_by_name(self, name, parent=None):
        return self.find_file_by_name(name, parent, self.IUnalignedReads)

    def find_variation_file_by_name(self, name, parent=None):
        return self.find_file_by_name(name, parent, self.IVariationFile)

    def find_experiment_by_name(self, name, parent=None):
        return self.find_file_by_name(name, parent, self.IExperiment)

    def find_application_page_file_by_name(self, name, parent=None):
        return self.find_file_by_name(name, parent, self.IApplicationPageFile)

    def collect_initializable_files_in_container(self, accession):
        """
        Recursively search for all initialisable file in container.

        :param accession: accession of container
        :return: list of accessions
        """
        return self.invoke('collectInitializableFilesInContainer', accession)

    def get_file_children(self, container_accession):
        """
        Return accessions of files linked to current container.

        :param container_accession:  accession of container
        :return: list of accessions
        """
        return self.invoke('getFileChildren', container_accession)

    def create_folder(self, name, parent=None, accession=None, description=None, metainfo=None):
        """
        Create folder.

        :param name: display name
        :param parent: if not specified create folder in 'private'
        :param accession: new folder accession, should be unique among platform.
        :param description: description for folder
        :param metainfo: additional Metainfo.
               description and accession should be specified via arguments or in metainfo, not in both places.
        :return: accession of created folder
        """
        metainfo = metainfo or Metainfo()
        metainfo.add_string(Metainfo.NAME, name)
        if description is not None:
            metainfo.add_string(Metainfo.DESCRIPTION, description)
        if accession is not None:
            metainfo.add_string(Metainfo.ACCESSION, accession)
        return self.invoke('createFolder', parent, metainfo)

    def find_or_create_folder(self, name, parent=None):
        """
        Return folder accession if it is already exists, create it otherwise.
        If more than one folder is found the first one is returned.

        :param name: display name
        :param parent: if not specified create folder in 'private'
        :return: accession of folder
        """
        return self.invoke('findOrCreateFolder', name, parent)

    def link_file(self, accession, parent):
        """
        Link file to folder.

        :param accession: file accession
        :param parent: destination accession
        """
        self.invoke('linkFile', accession, parent)

    def unlink_file(self, accession, parent):
        """
        Unlink file from folder.

        :param accession: file accession
        :param parent: folder accession
        """
        self.invoke('unlinkFile', accession, parent)

    def clear_container(self, container_accession):
        """
        Unlink all files from current container.

        :param container_accession: accession of the container
        """
        self.invoke('clearContainer', container_accession)

    def add_metainfo_string_value(self, accession_list, key, value):
        """
        Add string value to metainfo of specified files.

        :param accession_list: list of files to be updated
        :param key: metainfo key
        :param value: string
        """
        self.invoke('addMetainfoStringValue', accession_list, key, value)

    def replace_metainfo_string_value(self, accession_list, key, value):
        """
        Replace string value to metainfo of specified files.

        :param accession_list: list of files to be updated
        :param key: metainfo key
        :param value: string
        """
        self.invoke('replaceMetainfoStringValue', accession_list, key, value)

    def remove_metainfo_value(self, accession_list, key):
        """
        Delete key from metainfo of specified files.

        :param accession_list: list of files to be updated
        :param key: metainfo key
        """
        self.invoke('removeMetainfoValue', accession_list, key)

    def get_special_folder(self, name):
        """
        Return special folder accession.
        Available special folders:
          SpecialFolders.IMPORTED folder where new files are created by Data Importers
          SpecialFolders.CREATED default folder for files created by prepossessing and analyzing applications
          SpecialFolders.TEMPORARY temporary files
          SpecialFolders.UPLOADED  files there raw files are stored.

        :param name: special folder name
        :return: accession
        :raise GenestackException: if folder name is unknown
        """
        special_folders = (SpecialFolders.IMPORTED, SpecialFolders.CREATED, SpecialFolders.TEMPORARY,
                           SpecialFolders.UPLOADED)
        if not name in special_folders:
            raise GenestackException("Name '%s' must be one of %s" % (name, ', '.join(special_folders)))
        return self.invoke('getSpecialFolder', name)

    def share_files(self, accessions, group, destination_folder=None, password=None):
        """
        Share files.

        :param accessions: files accessions
        :param group: group to share
        :param destination_folder: folder there shared files to be linked. No links if folder is None
        :param password: password for share,
               if not specified will be asked in interactive prompt (work only if output redirected to terminal)
        """
        SudoUtils(self.connection).ensure_sudo_interactive(password)
        share_utils = self.connection.application('shareutils')
        share_utils.invoke('shareFilesForViewing', accessions, [group])
        if destination_folder is not None:
            share_utils.invoke('linkFiles', accessions, destination_folder, group)

    def get_groups_to_share(self):
        """
        Return dict for:  group_accession: group_info_dict

         group info keys:
             savedFolderName:
             savedFolderAccession:
             name:   group name
             folderName: name of shared group folder
             folderAccession: accessing of shared group folder

        """
        share_utils = self.connection.application('shareutils')
        return share_utils.invoke('getGroupsToShare')

    def get_folder(self, parent, *names, **kwargs):
        """
        Finds path recursively. As first argument it accepts any accession.
        Use PRIVATE for user folder, PUBLIC for public data. Parent folder must exist.
        For each path in path corresponding folder founded.  If folder is not found exception raised,
        except key "create=True" specified. In that case all folders will be created.

        :param parent: parent accession
        :param names: tuple of folder names that should be founded/created
        :param created: set True if missed folder should be created, default=False
        :return: accession of last folder in paths.
        :raise GenestackException: when paths are not specified or parent cant be found.
        """
        if not names:
            raise GenestackException("At least one path should be specified.")

        create = bool(kwargs.get('create'))
        for path in names:
            if create:
                parent = self.find_or_create_folder(path, parent=parent)
            else:
                _parent_accession = self.find_folder_by_name(path, parent=parent)
                if _parent_accession is None:
                    raise Exception('Cant find folder with name "%s" in folder with accession: %s' % (path, parent))
                parent = _parent_accession
        return parent
