FilesUtil
**********


File utils used for common file operations: find, link, remove and share.

You need to create instance::

    from genestack import FilesUtil, get_connection


    connection = get_connection()
    file_utils = FilesUtil(connection)

Create folder::

   folder_accession = file_utils.create_folder("My new folder")
   print folder_accession

This method creates folder in user folder. You can specify any folder you want as parent::

    inner_folder_accession = file_utils.create_folder("My new folder", parent=folder_accession)
    print inner_folder_accession


Find folder::

    folder_accession = file_utils.find_file_by_name("My new folder", file_class=FilesUtil.IFolder)
    print folder_accession


See :doc:`../applications/FilesUtil` for more info.
