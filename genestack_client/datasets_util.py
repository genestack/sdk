# -*- coding: utf-8 -*-

from genestack_client import Application, FilesUtil, SpecialFolders, Metainfo, GenestackException


class DatasetsUtil(Application):
    APPLICATION_ID = 'genestack/datasetsUtil'

    BATCH_SIZE = 100

    def create_dataset(self, name, dataset_type, children, parent=None, dataset_metainfo=None):
        """
        Create a dataset.

        :param name: name of the dataset
        :type name: str
        :param dataset_type: type of the dataset (children files interface name, must extend IDataFile)
        :type dataset_type: str
        :param children: list of children accessions
        :type children: list[str]
        :param parent: folder for the new dataset, 'My datasets' if not specified
        :type parent: str
        :param dataset_metainfo: metainfo of the created dataset
        :type dataset_metainfo: Metainfo

        :return: dataset accession
        :rtype: str
        """
        if parent is None:
            parent = self.__get_mydatasets_folder()

        dataset_metainfo = self._fill_dataset_metainfo(dataset_metainfo, name)

        return self.invoke('createDataset', parent, dataset_type, dataset_metainfo, children)

    def create_empty_dataset(self, name, dataset_type, parent=None, dataset_metainfo=None):
        """
        Create an empty dataset.

        :param name: name of the dataset
        :type name: str
        :param dataset_type: type of the dataset (children files interface name, must extend IDataFile)
        :type dataset_type: str
        :param parent: folder for the new dataset, 'My datasets' if not specified
        :type parent: str
        :param dataset_metainfo: metainfo of the created dataset
        :type dataset_metainfo: Metainfo

        :return: dataset accession
        :rtype: str
        """

        if parent is None:
            parent = self.__get_mydatasets_folder()

        dataset_metainfo = self._fill_dataset_metainfo(dataset_metainfo, name)

        return self.invoke('createEmptyDataset', parent, dataset_type, dataset_metainfo)

    @staticmethod
    def _fill_dataset_metainfo(dataset_metainfo, name):
        dataset_metainfo = dataset_metainfo or Metainfo()
        if Metainfo.NAME in dataset_metainfo:
            raise GenestackException(
                'Provided metainfo must not have "%s" field set' % Metainfo.NAME
            )

        dataset_metainfo.add_string(Metainfo.NAME, name)
        return dataset_metainfo

    def get_dataset_size(self, accession):
        """
        Get number of files in dataset.

        :param accession: dataset accession
        :type accession: str

        :return: number of files in dataset
        :rtype: int
        """
        return self.invoke('getDatasetSize', accession)

    def get_dataset_children(self, accession):
        """
        Return generator over children accessions of the provided dataset.

        :param accession: dataset accession
        :type accession: str
        :return: generator over dataset's children accessions
        """
        count = 0
        while True:
            children = self.invoke('getDatasetChildren', accession, count, self.BATCH_SIZE)
            for child in children:
                yield child

            count += len(children)
            if len(children) < self.BATCH_SIZE:
                break

    def create_subset(self, accession, children, parent=None):
        """
        Create a subset from dataset's children.

        :param accession: dataset accession
        :type accession: str
        :param children: list of children accessions to create a subset
        :type children: list[str]
        :param parent: folder for the new dataset, 'My datasets' if not specified
        :type parent: str

        :return: accession of the created subset
        :rtype: str
        """
        if parent is None:
            parent = self.__get_mydatasets_folder()

        return self.invoke('createSubset', parent, accession, children)

    def add_dataset_children(self, accession, children):
        """
        Add new files to a dataset.

        :param accession: dataset accession
        :type accession: str
        :param children: list of children accessions to add to the dataset
        :type children: list[str]
        """
        return self.invoke('addFiles', accession, children)

    def add_file_to_datasets(self, file_accession, dataset_accessions):
        """
        Add given file to several datasets.

        :param file_accession: file accession
        :type file_accession: str
        :param dataset_accessions: accessions of the datasets
        :type dataset_accessions: list[str]
        """
        return self.invoke('addFileToDatasets', file_accession, dataset_accessions)

    def remove_dataset_children(self, accession, children):
        """
        Remove children from dataset.

        :param accession: dataset accession
        :type accession: str
        :param children: list of children accessions to remove from the dataset
        :type children: list[str]
        """
        return self.invoke('removeFiles', accession, children)

    def merge_datasets(self, datasets, parent=None):
        """
        Create a new dataset from the given datasets.

        :param datasets: list of source datasets accessions
        :type datasets: list[str]
        :param parent: folder for the new dataset, 'My datasets' if not specified
        :type parent: str

        :return: accession of the created dataset
        :rtype: str
        """
        if parent is None:
            parent = self.__get_mydatasets_folder()

        return self.invoke('mergeDatasets', parent, datasets)

    def __get_mydatasets_folder(self):
        """
        Get default folder for datasets.

        :return: default dataset folder accession
        :rtype: str
        """
        return FilesUtil(self.connection).get_special_folder(SpecialFolders.MY_DATASETS)
