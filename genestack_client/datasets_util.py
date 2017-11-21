# -*- coding: utf-8 -*-

from genestack_client import Application, FilesUtil, SpecialFolders


class DatasetsUtil(Application):
    APPLICATION_ID = 'genestack/datasetsUtil'

    def create_dataset(self, name, dataset_type, children, parent=None):
        """
        Create a dataset.

        :param name: name of the dataset
        :type name: str
        :param dataset_type: type of the dataset
        :type dataset_type: str
        :param children: list of children accessions
        :type children: list[str]
        :param parent: folder for the new dataset, 'My datasets' if not specified
        :type parent: str

        :return: dataset accession
        :rtype: str
        """
        if parent is None:
            parent = self.__get_mydatasets_folder()

        return self.invoke('createDataset', parent, name, dataset_type, children)

    def get_dataset_size(self, accession):
        """
        Get number of files in dataset.

        :param accession: dataset accession
        :type accession: str

        :return: number of files in dataset
        :rtype: int
        """
        return self.invoke('getDatasetSize', accession)

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
