from odm_sdk import (Application, FileFilter, GenestackException, Metainfo,
                              validate_constant)

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
    DICTIONARY_FILE = 'com.genestack.api.files.IDictionaryFile'
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

    def find_dictionaries_by_name(self, name):
        """
        Finds the dictionaries that are not obsolete and have exactly the specified name.
        The search uses the search index, not the folders.

        :param name: dictionary name
        :type name: str
        :return: accessions of the dictionaries
        :rtype: list[str]
        """
        response = self.search_files(
            search_string=name,
            parameters={'type': self.DICTIONARY_FILE, 'name': name, 'obsolete': 'false'})
        return [accession
                for dictionary_file in response['files']
                for accession in dictionary_file['accessions']]

    def find_application_page_file_by_name(self, name, parent=None):
        return self.find_file_by_name(name, parent, self.APPLICATION_PAGE_FILE)

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
        :param *names: tuple of "path components", a hierarchy of folders to
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

    def search_files(self, search_string, parameters=None, data_types=None,
                     max_on_page=100, page_num=0, sort_order=None, ascending=False):
        """
        Search for files.

        :param search_string: search string (e.g. accession)
        :type search_string: str
        :param parameters: dictionary of search parameters
        :type parameters: dict[str, str]
        :param data_types: list of Java class names for file types
        :type data_types: list[str]
        :param max_on_page: maximum number of results per page
        :param page_num: page number
        :param sort_order: sort order (see SortOrder class)
        :param ascending: sort direction
        :return: list of file infos
        """
        parameters = parameters or {}
        data_types = data_types or []

        return self.invoke(
            'searchFiles',
            search_string,  # type: str
            parameters,     # type: dict
            data_types,     # type: list
            max_on_page,    # type: int
            page_num,       # type: int
            sort_order,     # type: str
            ascending       # type: bool
        )
