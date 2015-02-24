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


# Accession of private folder of current user.
PRIVATE = 'private'
# Accession for public folder
PUBLIC = 'public'


class SpecialFolders:
    """
    - IMPORTED: folder where new files are created by Data Importers
    - CREATED: default folder for files created by prepossessing and analyzing applications
    - TEMPORARY: temporary files
    - UPLOADED:  files there raw files are stored.
    """
    IMPORTED = 'imported'
    CREATED = 'created'
    TEMPORARY = 'temporary'
    UPLOADED = 'uploaded'


class FilesUtil(Application):
    """
    Application for file management.
    """
    APPLICATION_ID = 'genestack/filesUtil'

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
        :raises: GenestackServerException: if there is not or more then one reference genome
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
        :type accession: str
        :return: list of accessions
        :rtype: list
        """
        return self.invoke('collectInitializableFilesInContainer', accession)

    def get_file_children(self, container_accession):
        """
        Return accessions of files linked to current container.

        :param container_accession:  accession of container
        :type container_accession: str
        :return: list of accessions
        :rtype: list
        """
        return self.invoke('getFileChildren', container_accession)

    def create_folder(self, name, parent=None, description=None, metainfo=None):
        """
        Create folder.

        :param name: display name
        :type name: str
        :param parent: if not specified create folder in 'private'
        :type parent: str
        :param description: description for folder
        :type description: str
        :param metainfo: additional Metainfo. Description and accession should be specified via arguments or in metainfo, not in both places.
        :type metainfo: Metainfo
        :return: accession of created folder
        """
        metainfo = metainfo or Metainfo()
        metainfo.add_string(Metainfo.NAME, name)
        if description is not None:
            metainfo.add_string(Metainfo.DESCRIPTION, description)
        return self.invoke('createFolder', parent, metainfo)

    def find_or_create_folder(self, name, parent=None):
        """
        Return folder accession if it is already exists, create it otherwise.
        If more than one folder is found the first one is returned.

        :param name: display name
        :type name: str
        :param parent: parent accession, use home folder if None
        :type parent: str
        :return: accession of folder
        :rtype: str
        """
        return self.invoke('findOrCreateFolder', name, parent)

    def link_file(self, accession, parent):
        """
        Link file to folder.

        :param accession: file accession
        :type accession: str
        :param parent: destination accession
        :type parent: str
        :rtype: None
        """
        self.invoke('linkFile', accession, parent)

    def unlink_file(self, accession, parent):
        """
        Unlink file from folder.

        :param accession: file accession
        :type accession: str
        :param parent: folder accession
        :type parent: str
        :rtype: None
        """
        self.invoke('unlinkFile', accession, parent)

    def clear_container(self, container_accession):
        """
        Unlink all files from current container.

        :param container_accession: accession of the container
        :type container_accession: str
        :rtype: None
        """
        self.invoke('clearContainer', container_accession)

    def add_metainfo_string_value(self, accession_list, key, value):
        """
        Add string value to metainfo of specified files.

        :param accession_list: list of files to be updated
        :type accession_list: list
        :param key: metainfo key
        :type key: str
        :param value: string
        :type value: str
        :rtype: None
        """
        self.invoke('addMetainfoStringValue', accession_list, key, value)

    def replace_metainfo_string_value(self, accession_list, key, value):
        """
        Replace string value to metainfo of specified files.

        :param accession_list: list of files to be updated
        :type accession_list: list
        :param key: metainfo key
        :type key: str
        :param value: string
        :type value: str
        :rtype: None
        """
        self.invoke('replaceMetainfoStringValue', accession_list, key, value)

    def remove_metainfo_value(self, accession_list, key):
        """
        Delete key from metainfo of specified files.

        :param accession_list: list of files to be updated
        :type accession_list: list
        :param key: metainfo key
        :type key: str
        :rtype: None
        """
        self.invoke('removeMetainfoValue', accession_list, key)

    def get_special_folder(self, name):
        """
        Return special folder accession.

        Available special folders is described in :class:`.SpecialFolders`

        :param name: special folder name
        :type name: str
        :return: accession
        :rtype: str
        :raises: GenestackException: if folder name is unknown
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
        :type accessions: list
        :param group: group to share
        :type group: str
        :param destination_folder: folder there shared files to be linked. No links if folder is None
        :type destination_folder: str
        :param password: password for share, if not specified will be asked in interactive prompt (work only if output redirected to terminal)
        :type: str
        :rtype: None
        """
        SudoUtils(self.connection).ensure_sudo_interactive(password)
        share_utils = self.connection.application('genestack/shareutils')
        share_utils.invoke('shareFilesForViewing', accessions, [group])
        if destination_folder is not None:
            share_utils.invoke('linkFiles', accessions, destination_folder, group)

    def get_groups_to_share(self):
        """
        Return dict for:  group_accession: group_info_dict

        Group info keys:
        - savedFolderName:
        - savedFolderAccession:
        - name:   group name
        - folderName: name of shared group folder
        - folderAccession: accessing of shared group folder

        :return: group dict
        :rtype: dict

        """
        share_utils = self.connection.application('genestack/shareutils')
        return share_utils.invoke('getGroupsToShare')

    def get_folder(self, parent, *names, **kwargs):
        """
        Finds path recursively. As first argument it accepts any accession.
        Use PRIVATE for user folder, PUBLIC for public data. Parent folder must exist.
        For each path in path corresponding folder founded.  If folder is not found exception raised,
        except key ``create=True`` specified. In that case all folders will be created.

        :param parent: parent accession
        :type parent: str
        :param names: tuple of folder names that should be founded/created
        :type names: tuple
        :param created: set True if missed folder should be created, default is False
        :type created: bool
        :return: accession of last folder in paths.
        :rtype: str
        :raises:  GenestackException: when paths are not specified or parent cannot be found.
        """
        if not names:
            raise GenestackException("At least one path should be specified.")

        create = bool(kwargs.get('create'))
        for path in names:
            if create:
                parent = self.find_or_create_folder(path, parent=parent)
            else:
                _parent_accession = self.find_file_by_name(path, parent=parent, file_class=self.IFolder)
                if _parent_accession is None:
                    raise Exception('Cant find folder with name "%s" in folder with accession: %s' % (path, parent))
                parent = _parent_accession
        return parent
