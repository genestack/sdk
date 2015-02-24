FilesUtil
**********


File utils used for common file operations: find, link, remove and share.

To work with FilesUtil you need to connection::

    >>> from genestack import get_connection
    >>> connection = get_connection()

Create instance::

    >>> from genestack import FilesUtil
    >>> file_utils = FilesUtil(connection)


Create folder in user folder::

    >>> folder_accession = file_utils.create_folder("My new folder")
    >>> print folder_accession
    GSF000001

You can specify any folder you want as parent::

    >>> inner_folder_accession = file_utils.create_folder("My inner folder", parent=folder_accession)
    >>> print inner_folder_accession
    GSF000002


Find folder by its name::

    >>> folder_accession = file_utils.find_file_by_name("My inner folder", file_class=FilesUtil.IFolder)
    >>> print folder_accession
    GSF000002


See :doc:`../applications/FilesUtil` for more methods.
