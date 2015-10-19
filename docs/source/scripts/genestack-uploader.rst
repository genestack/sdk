
genestack-uploader
=====================

``genestack-uploader`` is installed with the Python Client Library and can be accessed from a terminal by typing ``genestack-uploader``.

.. WARNING!!! Don not edit part from below, it is auto-generated from script help output


Usage
-----
  .. code-block:: text

    usage: genestack-uploader [-h] [-H <host>] [-u <user>] [-p <password>] [-n]
                        <paths> [<paths> ...]
    
    Upload raw files to server and try to auto recognize them as genestack files.
    
    - Collecting files:
      Application can handle files and folder (will recursively collect all files).
      All paths must be valid. There is not limit to number of files.
    
    - Uploading:
      Files are stored in subfolder of 'Raw uploads'; subfolder name corresponds
      to user local time. Files are uploaded one by one, each in multiple threads.
      In case of network errors application attempts to retry until number of retries
      exceeded (5 by default), in which case application exits with error code.
      Uploaded data is not lost though and you can continue uploading this file
      from the point you stop.
    
      ATTENTION: When you upload multiple files from the command line,
      be sure to remove successfully uploaded files from the arguments when before re-running
      uploader, because otherwise all of them will be uploaded to the server again.
    
    - Recognition:
      Recognition done only if all files were uploaded successfully. It works over all files.
      Files that were not recognized are linked to subfolder 'Unrecognized files'.
    
      ATTENTION: Recognition of big number of files may cause server timeouts.
      Split uploading with recognition into relatively small iterations to prevent timeout
      failures.
    
    optional arguments:
      -h, --help            show this help message and exit
    
    connection:
      -H <host>, --host <host>
                            server host
      -u <user>             user alias from settings or email
      -p <password>         user password
    
    command arguments:
      <paths>               path to files or folders
      -n, --no-recognition  don't try to recognize files
    

