#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from genestack_client import *


# base class to create multiple files with a CLA
class BatchFilesCreator:
    def __init__(self, cla, base_folder, friendly_name, custom_args=None):
        """
        Constructor of the general batch files creator, to create multiple files from a CLA.

        :param cla: a ``CLApplication`` object, wrapper for the corresponding CLA
        :param base_folder: accession of the base folder where the pipeline files will be organized into subfolders
        :param friendly_name: user-friendly name of the files produced by the app ; used in the on-screen statements
        and in the name of the project subfolders
        :param custom_args: list of custom command-line argument strings for the files. Default is ``None``
        """

        self._cla = cla
        self._base_folder = base_folder
        self._friendly_name = friendly_name
        self._custom_args = custom_args

    def create_files(self, sources):
        print "Creating %s files..." % self._friendly_name
        output_folder = files_util.create_folder(self._friendly_name, parent=self._base_folder)
        output_files = []
        for i, source in enumerate(sources):
            output = self._create_output_file(source)
            files_util.link_file(output, output_folder)
            print "Created %s file %s (%d/%d)" % (self._friendly_name, output, i + 1, n_files)
            output_files.append(output)
        return output_files

    # this method can be overriden in child classes to allow for more complex file creation logic
    def _create_output_file(self, source):
        output = self._cla.create_file(source)
        if self._custom_args:
            self._cla.change_command_line_arguments(output, self._custom_args)
        return output


# special class for Bowtie to replace the default reference genome
class BowtieBatchFilesCreator(BatchFilesCreator):
    def __init__(self, cla, base_folder, friendly_name, custom_args=None, ref_genome=None):
        BatchFilesCreator.__init__(self, cla, base_folder, friendly_name, custom_args)
        self._ref_genome = ref_genome
        self._files_util = FilesUtil(cla.connection)

    def _create_output_file(self, source):
        output = BatchFilesCreator._create_output_file(self, source)
        # replace reference genome
        if self._ref_genome:
            self._files_util.remove_metainfo_value([output], BioMetainfo.REFERENCE_GENOME)
            self._cla.replace_file_reference(output, BioMetainfo.REFERENCE_GENOME, None, self._ref_genome)
        return output

# these are the CLA arguments that correspond to all default options except the type of variants to look for (SNPs only)
# the easiest way to know the syntax of the command-line arguments for a specific app is to look at the "Parameters"
# metainfo field of a CLA file on Genestack that has the parameters you want
VC_ARGUMENTS_NO_INDELS = ["--skip-indels -d 250 -m 1 -E --BCF --output-tags DP,DV,DP4,SP", "",
                          "--skip-variants indels --multiallelic-caller --variants-only"]

if __name__ == "__main__":
    # parse script arguments
    parser = make_connection_parser()
    parser.add_argument('raw_reads_folder',
                        help='Genestack accession of the folder containing the raw reads files to process.')
    parser.add_argument('--name', help='Name of the Genestack folder where to put the output files')
    parser.add_argument('--ref-genome', help='Accession of the reference genome to use for the mapping step')

    args = parser.parse_args()
    project_name = args.name or "New Project"

    print "Connecting to Genestack..."

    # get connection and application handlers
    connection = get_connection(args)
    bowtie_app = BowtieApplication(connection)
    mapped_qc_app = AlignedReadsQC(connection)
    variant_calling_app = VariationCaller2Application(connection)
    files_util = FilesUtil(connection)

    created_files_folder = files_util.get_special_folder(SpecialFolders.CREATED)

    # collect files
    print "Collecting raw reads..."
    raw_reads = files_util.get_file_children(args.raw_reads_folder)
    n_files = len(raw_reads)
    print "Found %d files to process" % n_files

    base_folder = files_util.create_folder(project_name, parent=created_files_folder)

    # Create pipeline files
    bowtie_creator = BowtieBatchFilesCreator(bowtie_app, base_folder, "Mapped Reads", ref_genome=args.ref_genome)
    mapped_reads = bowtie_creator.create_files(raw_reads)
    mapped_reads_qcs = BatchFilesCreator(mapped_qc_app, base_folder, "Mapped Reads QC").create_files(mapped_reads)
    vc_creator = BatchFilesCreator(variant_calling_app, base_folder, "Variants", custom_args=VC_ARGUMENTS_NO_INDELS)
    vc_creator.create_files(mapped_reads)

    print "All done! Your files are in the folder %s" % base_folder
