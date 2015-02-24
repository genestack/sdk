Importers
*********

Script to load experiment with unaligned read file:

    .. literalinclude:: code/import_file.py

Run script:

  .. code-block:: sh

    % ./examples_code.py
    Uploading ds1.gz - 100.00%
    Uploading ds2.gz - 100.00%
    Successfully load file with accession GSF000148
    Start initialization of GSF000148

As result you will get ``unaligned read`` file and two ``raw files`` in ``Upload`` folder.
  Raw files are required for initialization, after initialization successfully completed you can remove them.
  If you pass valid public url as link you will not get raw files.


Supported url formats
=====================
   if file is ended on .gz it is treated as gz archive. Bot packed and unpacked files will produce same result.

* ``file://`` (default for not specified):
    - ``test.txt.gz``
    - ``file://test.txt``

* ``ftp://``
    - ``ftp://server.com/file.txt``

* ``http://`` ``https://``
    - ``http://server.com/file.txt``

* ``ascp://``
    - ``ascp://<user>@<server>:file.txt``
