Sample Scripts
##############

This section provides reusable examples of scripts that allow you to perform actions on Genestack that would be tedious to accomplish through the web interface, such as multiple file uploads with custom metadata.

Retrieving task logs
--------------------

This is a simple script to retrieve and print the logs of an initialization task on Genestack.

.. literalinclude:: sample_scripts/get_task_logs.py
    :linenos:
    :language: python

The script connects to Genestack and uses the ``TaskLogViewer`` class defined in the client library, to retrieve the
logs for a file whose accession should be passed as a command-line parameter to the script.

``TaskLogViewer`` is a child class of ``Application``, and it provides an interface to the Genestack application
``genestack/task-log-viewer`` which exposes a public Java method (``getFileInitializationLog``) to access the
initialization logs of a file.

Uploading multiple files with custom metainfo
---------------------------------------------

A typical situation when you want to upload data is that you have some raw sequencing files somewhere
(on an FTP site, on your local computer, etc.) and a spreadsheet with information about these files,
that you would want to record in Genestack.

So let's imagine that we have a comma-delimited CSV file with the following format:

.. code-block:: none

    name,organism,disease,link
    HPX12,Homo sapiens,lung cancer,ftp://my.ftp/raw_data/HPX12_001.fq.gz
    HPZ24,Homo sapiens,healthy,ftp://my.ftp/raw_data/HPZ24_001.fq.gz
    .........

Now let's write a Python script that uses the Genestack Client Library to upload these files to
a Genestack instance, with the right metainfo. The script will take as input the CSV file,
and create a Genestack Experiment with a Sequencing Assay for each row of the CSV file.

.. literalinclude:: sample_scripts/make_experiment_from_csv.py
    :linenos:
    :language: python

This script uses many features from the client library:

    * we start by adding arguments to the argument parser to process our metadata file
    * then we establish a connection to Genestack, and instantiate a ``DataImporter`` to be able to create our files on Genestack
    * we create the experiment where we will store our data
    * we parse the CSV file using a Python ``csv.DictReader``, create a new metainfo object for each row and a corresponding Sequencing Assay with that metainfo

We can then run the script like this:

.. code-block:: shell

    python make_experiment_from_csv.py --name "My experiment" --description "My description" my_csv_metadata_file.csv


The metainfo of each Sequencing Assay specified inside the CSV file needs to contain at least a ``name`` and valid ``link`` (either to a local or a remote file). By default, the experiment will be created inside the user's ``Imported Files`` folder on Genestack, since we haven't specified a folder.

.. note::

    One could easily extend this script to support two files per sample (in the case of paired-end reads).

Importing ENCODE RNA-seq data
------------------------------

We can extend the previous script to download data from the `ENCODE project <https://www.encodeproject
.org/matrix/?type=Experiment>`__ .
If we select a list of experiments from the ENCODE experiment matrix, we can obtain a link to a CSV file which contains
all the metadata and data for the matching assays. For instance, this is the link for
`all FASTQ files for human RNA-seq experiments <https://www.encodeproject.org/metadata/type=Experiment&replicates
.library.biosample.donor.organism.scientific_name=Homo+sapiens&files.file_type=fastq&assay_title=RNA-seq/metadata
.tsv>`__ .

By browsing this TSV file, we see that it contains the following useful fields:

    * ``File accession``
    * ``Experiment accession``
    * ``Biosample sex``
    * ``Biosample organism``
    * ``Biosample term name``: cell line or tissue
    * ``Biosample Age``
    * ``Paired with``: if the sample was paired-end, this field points to the file accession of the other mate

We also notice that file download URLs always follow the template:

.. code-block:: none

    https://www.encodeproject.org/files/<FILE_ACCESSION>/@@download/<FILE_ACCESSION>.fastq.gz

We can use this observation to generate the reads URLs from the fields ``File accession`` and possibly ``Paired with``.
We use the following logic: we read through the metadata file, while keeping a set of all the accessions of the
paired FASTQ files handled so far.
If the current line corresponds to a file that has already been created (second mate of a paired-end
file), then we skip it. Otherwise we prepare a metainfo object for the file and create the Genestack file.

If the row contains a ``Paired with`` accession, we also add the corresponding URL to the current metadata, and add
the accession to the set of FASTQ files seen so far.

.. literalinclude:: sample_scripts/import_encode_data.py
    :linenos:
    :language: python

Editing the metainfo of existing files
--------------------------------------

In the real world, data and metadata live in different places and you may not have access to both of them at the same time.
Sometimes, you may be in a situation where you have uploaded data on Genestack and you are only provided with metadata later on.
The following script takes as input a comma-delimited CSV
file containing metadata and adds that metadata to existing files on Genestack. The files should be located in a
specific folder, and the correspondence between records in the CSV file and the remote files is determined by the
name of the remote files. The name of the files should be stored in a specific column of the CSV file,
whose name must be supplied to the script as ``local-key`` parameter.

.. literalinclude:: sample_scripts/add_metainfo_from_table.py
    :linenos:
    :language: python

For instance, imagine we have the following CSV file:

.. code-block:: none

    file_name,organism,disease
    Patient 1,Homo sapiens,Asthma
    Patient 2,Homo sapiens,Healthy
    ....

The script is then called with the following syntax:

.. code-block:: shell

    python add_metainfo_from_table.py my_csv_file.csv file_name GSF12345


Organising files into folders based on their metainfo
-----------------------------------------------------

Keeping your files organised is a difficult thing. A common thing to do when you have many files belonging to the same
project is to group them into folders based on their application.
The following script takes as input a folder of files and organises these files into subfolders, such that all files
created with the same application will go into the same subfolder. We will also provide an option to unlink the files from
their folder of origin. The script illustrates the use of the :ref:`FilesUtil` class to perform
typical file manipulation operations.

.. literalinclude:: sample_scripts/group_files_into_folders.py
    :linenos:
    :language: python

The script can be called with the following syntax:

.. code-block:: shell

    python group_files_into_folders.py [--move-files] <source_folder_accession>

You can easily adapt the script to group files based on some other criterion from their metainfo, like their organism, their
creation date, or in fact any metainfo value.
