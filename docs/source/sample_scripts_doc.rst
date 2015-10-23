Sample Scripts
##############

This section provides reusable examples of scripts that allow you to perform actions on Genestack that would be tedious to accomplish through the web interface, such as multiple file uploads with custom metadata.

Uploading multiple files with custom metainfo
---------------------------------------------

A typical situation when you want to upload data is that you have some raw sequencing files somewhere (on an FTP site, on your local computer, etc.) and a spreadsheet with information about these files, that you would want to record in Genestack.

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

Running a data analysis pipeline
--------------------------------

Generally, if you want to run multiple files through the same analysis pipeline, the easiest way to do it is using the Data Flow Editor through the web interface. This tool is powerful enough to cover most of the use cases you could think of.
However, some complex pipelines are not supported by the Data Flow Editor. In that case, you can write your own script to generate all the files on Genestack programmatically.

Our script will take as input the Genestack accession of a folder containing Unaligned Reads files. It will then produce for each file three downstream files: a Mapped Reads file produced with Bowtie (possibly using a custom reference genome), a Mapped Reads QC Report, and a Variant Calling file.

To do this, we define a ``BatchFilesCreator`` class with some simple methods to create multiple files from a CLA. We also create a ``BowtieBatchFilesCreator`` inheriting from this class, that has additional logic to change the reference genome. You can easily adapt this logic to your own pipeline.

Moreover, we will create Variant Calling files with non-default parameter (specifically, we only want to call SNPs and not indels). To do this, we use the method ``CLApplication.change_command_line_arguments``, which takes as input the accession of the CLA file, and the list of command-line strings to use.

Since the syntax of the command-line strings can vary from one CLA to another, the easiest way to know what command-line strings you should specify is to first create a file with the corresponding CLA on Genestack and change the parameters to the ones you want using the user interface. Then, look at the metainfo of the file (for example by clicking the name of the file inside the CLA page and choosing "View metainfo"). The metainfo field "Parameters" will store the list of command-line strings that you want (strings are separated by commas in the Metainfo Viewer dialog).

.. note::

    File references (like reference genomes) are not specified in the parameters strings. They are stored in separate metainfo fields. The code for ``BowtieBatchFilesCreator`` illustrates how to use a custom reference genome for the Bowtie-based Unspliced Mapping CLA.


.. literalinclude:: sample_scripts/run_vc_pipeline.py
    :linenos:
    :language: python

The script can then be called from a terminal with the following syntax:

.. code-block:: shell

    python run_vc_pipeline.py -u <user_alias> --ref-genome <custom_ref_genome_accession> --name "My project name" <raw_reads_folder>

Note that the folder supplied as input to the script should **only** contain Unaligned Reads files.
