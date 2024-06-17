from odm_sdk import (Application, FileFilter, GenestackException, Metainfo,
                              validate_constant)

CALCULATE_CHECKSUMS_KEY = 'genestack.checksum:markedForTests'
EXPECTED_CHECKSUM_PREFIX = 'genestack.checksum.expected:'
FILE_BATCH_SIZE = 500


class SpecialFolders(object):
    """
    - ``IMPORTED``: folder with files created by Data Importers
    - ``CREATED``: folder with files created by ``Preprocess`` and ``Analyse`` applications
    - ``TEMPORARY``: folder with temporary files
    - ``UPLOADED``: folder with uploaded raw files
    - ``MY_DATASETS``: folder with created datasets
    """
    IMPORTED = 'imported'
    CREATED = 'created'
    TEMPORARY = 'temporary'
    UPLOADED = 'uploaded'
    MY_DATASETS = 'my datasets'


class SortOrder(object):
    """
    Sort orders for file search queries
    """
    BY_NAME = "BY_NAME"
    BY_ACCESSION = "BY_ACCESSION"
    BY_LAST_UPDATE = "BY_LAST_UPDATE"
    DEFAULT = "DEFAULT"


class FilesUtil(Application):
    """
    An application to perform file management operations on Genestack.
    """
    APPLICATION_ID = 'genestack/filesUtil'

    CONTAINER = 'com.genestack.api.files.IContainerFile'
    FOLDER = 'com.genestack.api.files.IFolder'
    EXPERIMENT = 'com.genestack.bio.files.IExperiment'
    DATASET = 'com.genestack.api.files.IDataset'

    FILE = 'com.genestack.api.files.IFile'
    UNALIGNED_READS = 'com.genestack.bio.files.IUnalignedReads'
    UNALIGNED_READS_DATA = 'com.genestack.bio.files.IUnalignedReadsData'
    ALIGNED_READS = 'com.genestack.bio.files.IAlignedReads'
    VARIATION_FILE = 'com.genestack.bio.files.IVariationFile'
    APPLICATION_PAGE_FILE = 'com.genestack.api.files.IApplicationPageFile'
    REFERENCE_GENOME = 'com.genestack.bio.files.IReferenceGenome'
    AUXILIARY_FILE = 'com.genestack.api.files.IAuxiliaryFile'
    INDEX_FILE = 'com.genestack.api.files.IIndexFile'
    CODON_TABLE = 'com.genestack.bio.files.ICodonTable'
    GENOME_BED_DATA = 'com.genestack.bio.files.genomedata.IGenomeBEDData'
    GENOME_WIGGLE_DATA = 'com.genestack.bio.files.genomedata.IGenomeWiggleData'
    GENOME_ANNOTATIONS = 'com.genestack.bio.files.IGenomeAnnotations'
    HTSEQ_COUNTS = 'com.genestack.bio.files.IHTSeqCounts'
    EXTERNAL_DATABASE = 'com.genestack.bio.files.IExternalDataBase'
    PREFERENCES_FILE = 'com.genestack.api.files.IPreferencesFile'
    REPORT_FILE = 'com.genestack.api.files.IReportFile'
    RAW_FILE = 'com.genestack.api.files.IRawFile'
    MICROARRAY_ASSAY = 'com.genestack.bio.files.IMicroarrayAssay'
    MICROARRAY_DATA = 'com.genestack.bio.files.IMicroarrayData'
    SEQUENCING_ASSAY = 'com.genestack.bio.files.ISequencingAssay'
    FEATURE_LIST = 'com.genestack.bio.files.IFeatureList'
    EXPRESSION_SIGNATURE = 'com.genestack.bio.files.IGeneExpressionSignature'
    EXPRESSION_LEVELS = 'com.genestack.bio.files.IExpressionLevels'

    MAX_FILE_SEARCH_LIMIT = 2000
    MAX_RELATED_TERMS_LIMIT = 10000

    def find_reference_genome(self, organism, assembly, release):
        """
        Returns the accession of the reference genome with the specified parameters:
        ``organism``, ``assembly``, ``release``.
        If more than one or no genome is found, the corresponding exceptions are thrown.

        :param organism: organism
        :type organism: str
        :param assembly: assembly
        :type assembly: str
        :param release: release
        :type release: str
        :return: accession
        :rtype: str
        :raises: :py:class:`~odm_sdk.exceptions.GenestackServerException`
                 if more than one genome, or no genome is found
        """
        return self.invoke('findReferenceGenome', organism, assembly, release)

    def find_file_by_name(self, name, parent=None, file_class=FILE):
        """
        Finds file with specified name (ignore case!) and type.
        If no file is found ``None`` is returned.
        If more than one file is found the first one is returned.
        If the parent container is not found, the corresponding exceptions are thrown.

        :param name: file name
        :type name: str
        :param parent: parent accession, private folder is default
        :type parent: str
        :param file_class: File class to be returned, default IFile
        :type file_class: str
        :return: file accession
        :rtype: str
        """
        return self.invoke(
            'getFileByName',
            name, parent, file_class
        )

    # SA: TODO: remove this methods and change usage to findFileByName
    def find_folder_by_name(self, name, parent=None):
        return self.find_file_by_name(name, parent, self.FOLDER)

    def find_aligned_reads_file_by_name(self, name, parent=None):
        return self.find_file_by_name(name, parent, self.ALIGNED_READS)

    def find_unaligned_reads_file_by_name(self, name, parent=None):
        return self.find_file_by_name(name, parent, self.UNALIGNED_READS)

    def find_variation_file_by_name(self, name, parent=None):
        return self.find_file_by_name(name, parent, self.VARIATION_FILE)

    def find_experiment_by_name(self, name, parent=None):
        return self.find_file_by_name(name, parent, self.EXPERIMENT)

    def find_application_page_file_by_name(self, name, parent=None):
        return self.find_file_by_name(name, parent, self.APPLICATION_PAGE_FILE)

    # FIXME: use pagination in this method, see #5063
    def collect_initializable_files_in_container(self, accession):
        """
        Recursively search for all initialisable file in container.

        :param accession: accession of container
        :type accession: str
        :return: list of accessions
        :rtype: list
        """
        return self.invoke('collectInitializableFilesInContainer', accession)

    def count_file_children(self, container_accession):
        """
        Count children of a container (not recursive).
        :param container_accession: accession of container
        :type container_accession: str
        :return: number of children
        :rtype int:
        """
        return self.invoke('countFileChildren', container_accession)

    def get_file_children(self, container_accession):
        """
        Return accessions of files linked to current container.

        :param container_accession:  accession of container
        :type container_accession: str
        :return: list of accessions
        :rtype: list
        """
        all_files = []
        count = 0
        while True:
            batch = self.invoke('getFileChildren', container_accession, count, FILE_BATCH_SIZE)
            all_files += batch
            count += len(batch)
            if len(batch) < FILE_BATCH_SIZE:
                break
        return all_files

    def create_folder(self, name, parent=None, description=None, metainfo=None):
        """
        Create a folder.

        :param name: name of the folder
        :type name: str
        :param parent: if not specified, create folder in the user's private folder
        :type parent: str
        :param description: description of the folder (goes into the metainfo)
        :type description: str
        :param metainfo: additional :py:class:`~odm_sdk.Metainfo`.
            Description and accession should be specified either via arguments or in a metainfo object (but not in both).
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
        Return the folder accession if it already exists, and create it otherwise.
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
        Link a file to a folder.

        :param accession: file accession
        :type accession: str
        :param parent: parent folder accession
        :type parent: str
        :rtype: None
        """
        self.invoke('linkFiles', {accession: [parent]})

    def unlink_file(self, accession, parent):
        """
        Unlink a file from a folder.

        :param accession: file accession
        :type accession: str
        :param parent: folder accession
        :type parent: str
        :rtype: None
        """
        self.invoke('unlinkFiles', {accession: [parent]})

    def link_files(self, children_to_parents_dict):
        """
        Link files to containers.

        :param children_to_parents_dict: dictionary where keys are accessions of the files to link, and
            values are lists of accessions of the containers to link into
        :type: dict

        :rtype: None
        """
        self.invoke('linkFiles', children_to_parents_dict)

    def unlink_files(self, children_to_parents_dict):
        """
        Unlink files from containers.

        :param children_to_parents_dict: dictionary where keys are accessions of the files to unlink, and
            values are lists of accessions of the containers to unlink from
        :type children_to_parents_dict: dict[str, list[str]]
        :rtype: None
        """
        self.invoke('unlinkFiles', children_to_parents_dict)

    def add_metainfo_string_value(self, accession_list, key, value):
        """
        Add a string value to the metainfo of specified files.

        :param accession_list: list of files to be updated
        :type accession_list: list[str]
        :param key: metainfo key
        :type key: str
        :param value: string
        :type value: str
        :rtype: None
        """
        self.invoke('addMetainfoStringValue', accession_list, key, value)

    def replace_metainfo_string_value(self, accession_list, key, value):
        """
        Replace a string value in the metainfo of specified files.

        :param accession_list: list of files to be updated
        :type accession_list: list[str]
        :param key: metainfo key
        :type key: str
        :param value: string
        :type value: str
        :rtype: None
        """
        self.invoke('replaceMetainfoStringValue', accession_list, key, value)

    def replace_metainfo_value(self, accession_list, key, value):
        """
        Replace a value in the metainfo of specified files.

        :param accession_list: list of files to be updated
        :type accession_list: list[str]
        :param key: metainfo key
        :type key: str
        :param value: metainfo value
        :type value: MetainfoScalarValue
        :rtype: None
        """
        self.invoke('replaceMetainfoValue', accession_list, key, value)

    def remove_metainfo_value(self, accession_list, key):
        """
        Delete a key from the metainfo of specified files.

        :param accession_list: list of files to be updated
        :type accession_list: list[str]
        :param key: metainfo key
        :type key: str
        :rtype: None
        """
        self.invoke('removeMetainfoValue', accession_list, key)

    def add_metainfo_values(self, accession, metainfo, skip_existing_keys=True, replace_existing_keys=False):
        """
        Add metainfo to a specified file.
        By default, metainfo keys that are already present in the file will be skipped.

        :param accession: accession of the file to update
        :param metainfo: metainfo object containing the metainfo to add
        :type metainfo: Metainfo
        :param skip_existing_keys: ignore metainfo keys that are already present in the file's metainfo
            (default: ``True``)
        :type skip_existing_keys: bool
        :param replace_existing_keys: replace the existing metainfo value for the metainfo keys
            that are already present in the file's metainfo (default: ``False``)
        :type replace_existing_keys: bool
        :rtype: None
        """
        self.invoke('addMetainfoValues', accession, metainfo, skip_existing_keys, replace_existing_keys)

    def get_metainfo_values_as_strings(self, accessions_list, keys_list=None):
        """
        Retrieve metainfo values as strings for specific files and metainfo keys.
        Metainfo value lists are concatenated to string using ', ' as delimiter.
        The function returns a dictionary.

        :param accessions_list: accessions of the files to retrieve
        :type: accessions: list[str]
        :param keys_list: metainfo keys to retrieve (if ``None``, all non-technical keys are retrieved for each file)
        :type: keys: list[str]|None
        :return: a two-level dictionary with the following structure: accession -> key -> value
        :rtype: dict[str, dict[str, str]]
        """
        return self.invoke('getMetainfoValuesAsStrings', accessions_list, keys_list)

    def get_metainfo_values_as_string_list(self, accessions_list, keys_list=None):
        """
        Retrieve metainfo values as lists of strings for specific files and metainfo keys.
        The function returns a dictionary.

        :param accessions_list: accessions of the files to retrieve
        :type: accessions: list[str]
        :param keys_list: metainfo keys to retrieve (if ``None``, all non-technical keys are retrieved for each file)
        :type: keys: list[str]|None
        :return: a two-level dictionary with the following structure: accession -> key -> value list
        :rtype: dict[str, dict[str, list[str]]]
        """
        return self.invoke('getMetainfoValuesAsStringList', accessions_list, keys_list)

    def get_special_folder(self, name):
        """
        Return the accession of a special folder.

        Available special folders are described in :class:`.SpecialFolders`

        :param name: special folder name
        :type name: str
        :return: accession
        :rtype: str
        :raises: GenestackException: if folder name is unknown
        """
        special_folders = (SpecialFolders.IMPORTED, SpecialFolders.CREATED, SpecialFolders.TEMPORARY,
                           SpecialFolders.UPLOADED, SpecialFolders.MY_DATASETS)
        if name not in special_folders:
            raise GenestackException("Name '%s' must be one of %s" % (name, ', '.join(special_folders)))
        return self.invoke('getSpecialFolder', name)

    def get_group_folder_info(self, group_accession):
        raise NotImplementedError("FilesUtil.get_group_folder_info has been removed in v0.33")

    def get_folder(self, parent, *names, **kwargs):
        """
        Find a subfolder (by name) in a folder passed as an accession,
        returning accession of that subfolder.  If several names are provided,
        treat them as a path components for the sub-sub-...-folder down the
        folder hierarchy, returning accession of that deepmost folder:

        - ``fu.get_folder('GS777', 'RNASeq')`` looks for subfolder with *name*
          "RNASeq" in folder with *accession* "GS777", and returns accession of
          that "RNASeq" subfolder;

        - ``fu.get_folder('GS777', 'Experiments', 'RNASeq')`` looks for
          subfolder with *name* "Experiments" in a folder with *accession*
          "GS777", then looks for "RNASeq" in "Experiments", and returns the
          accession of "RNASeq".

        If ``create=True`` is passed as a *kwarg*, all the folders in ``names``
        hierarchy will be created (otherwise ``GenestackException`` is raised).

        :param parent: accession of folder to search in
        :type parent: str
        :param \*names: tuple of "path components", a hierarchy of folders to
                        find
        :type names: tuple
        :param create: whether to create folders from ``names`` if they don't
                       exist or not; default is ``False`` (raise
                       ``GenestackException`` if any folder doesn't exist)
        :type create: bool
        :return: accession of found (or created) subfolder
        :rtype: str
        :raises GenestackException:
            if no name is passed, or folder with required name is not found
            (and shouldn't be created)
        """
        if not names:
            raise GenestackException("At least one path should be specified")

        create = bool(kwargs.get('create'))
        for path in names:
            if create:
                parent = self.find_or_create_folder(path, parent=parent)
            else:
                _parent_accession = self.find_file_by_name(path, parent=parent, file_class=self.FOLDER)
                if _parent_accession is None:
                    raise GenestackException('Cannot find folder with name "%s" '
                                             'in folder with accession: %s'
                                             % (path, parent))
                parent = _parent_accession
        return parent

    def get_home_folder(self):
        """
        Return the accession of the current user's home folder.

        :return: accession of home folder
        :rtype: str
        """
        return 'private'

    def get_public_folder(self):
        """
        Return the accession of the ``Public`` folder on the current Genestack instance.

        :return: accession of ``Public`` folder
        :rtype: str
        """
        return 'public'

    def get_infos(self, accession_list):
        """
        Returns a list of dictionaries with information about each of the specified files.
        This will return an error if any of the accessions is not valid.
        The order of the returned list is the same as the one of the accessions list.

        The information dictionaries have the following structure:

            - accession
            - owner
            - name
            - isDataset
            - application

                - id

            - initializationStatus

                - isError
                - id

            - permissionsByGroup (the value for each key is a dictionary with group accessions as keys)

                - groupNames
                - ids

            - time

                - fileCreation
                - initializationQueued
                - initializationStart
                - initializationEnd
                - fileCreation
                - lastMetainfoModification


        :param accession_list: list of valid accessions.
        :type accession_list: list
        :return: list of file info dictionaries.
        :rtype: list[dict[str, object]]
        """
        return self.invoke('getInfos', accession_list)

    def rename_file(self, accession, name):
        """
        Rename a file.

        :param accession: file accession
        :type accession: str
        :param name: name
        :type name: str
        :rtype: None
        """
        self.invoke('renameFile', accession, name)

    def mark_for_tests(self, app_file):
        """
        Mark Genestack file as test one by adding corresponding key to metainfo.
        Test file will calculate md5 checksums of its encapsulated physical files
        during initialization.

        :param app_file: accession of file
        :return: None
        """
        metainfo = Metainfo()
        metainfo.add_boolean(CALCULATE_CHECKSUMS_KEY, True)
        self.add_metainfo_values(app_file, metainfo)

    def mark_obsolete(self, accession):
        """
        Mark Genestack file as obsolete one by adding corresponding key to metainfo.

        :param accession: accession of file
        :return: None
        """
        metainfo = Metainfo()
        metainfo.add_boolean('genestack:obsolete', True)
        self.add_metainfo_values(accession, metainfo)

    def add_checksums(self, app_file, expected_checksums):
        """
        Add expected MD5 checksum to the metainfo of a CLA file.
        Expected checksums are calculated in the following way:

            - The number of checksums equals number of entries in storage.
              For instance, a Reference Genome file has 2 entries (annotation and sequence files).
            - If there are multiple files in one entry, they will be concatenated in the same order
              as they were ``PUT`` to storage by the initialization script.
            - If a file is marked for testing, then after initialization its metainfo
              will contain both expected and actual checksum values.

        :param app_file: accession of application file
        :param expected_checksums: collection of MD5 checksums
        :return: None
        """
        metainfo = Metainfo()
        for key, value in expected_checksums.items():
            metainfo.add_string('%s%s' % (EXPECTED_CHECKSUM_PREFIX, key), value)
        self.add_metainfo_values(app_file, metainfo)

    def find_files(
            self,
            file_filter,
            sort_order=SortOrder.DEFAULT,
            ascending=False,
            offset=0,
            limit=MAX_FILE_SEARCH_LIMIT
    ):
        """
        Search for files with ``file_filter`` and return dictionary with two key/value pairs:

         - ``'total'``: total number (``int``) of files matching the query
         - ``'result'``: list of file info dictionaries for subset of matching files
                         (from ``offset`` to ``offset+limit``). See the documentation of
                         :py:meth:`~odm_sdk.FilesUtil.get_infos` for the structure
                         of these objects.

        :param file_filter: file filter
        :type file_filter: FileFilter
        :param sort_order: sorting order for the results,
                           see :py:class:`~odm_sdk.files_util.SortOrder`
        :type sort_order: str
        :param ascending: should the results be in ascending order? (default: False)
        :type ascending: bool
        :param offset: search offset (default: 0, cannot be negative)
        :type offset: int
        :param limit: maximum number of results to return (max and default: 100)
        :type limit: int
        :return: a dictionary with search response
        :rtype: dict[str, int|list[dict[str, str|dict]]]
        """
        limit = min(self.MAX_FILE_SEARCH_LIMIT, limit)
        if offset < 0 or limit < 0:
            raise GenestackException("Search offset/limit cannot be negative")
        if not validate_constant(SortOrder, sort_order):
            raise GenestackException("Invalid sort order")
        return self.invoke('findFiles', file_filter.get_dict(), sort_order, ascending, offset, limit)

    def collect_metainfos(self, accessions):
        """
        Get complete metainfo of a list of files.

        :param accessions: list of accessions
        :type accessions: list[str]
        :return: list of metainfo objects
        :rtype: list[Metainfo]
        """
        return [Metainfo.parse_metainfo_from_dict(mi)
                for mi in self.invoke('getMetainfo', accessions)]
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

    def search_files(self, accession):
        return self.invoke('searchFiles',
                           accession,  # type: str
                           {}, 100, 0, None, False)
