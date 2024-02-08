class GenomeQuery(object):
    """
    Class describing a genome query.
    """
    _DELIMITER = '|'

    class SortingOrder(object):
        BY_FDR = 'ByPValue'
        BY_LOG_FOLD_CHANGE = 'ByLogFoldChange'
        BY_LOG_COUNTS = 'ByLogCountsPerMillion'

    class Filter(object):
        MAX_FDR = 'maximumFDR'
        MIN_LOG_FOLD_CHANGE = 'minimumLogFoldChange'
        MIN_LOG_COUNTS = 'minimumLogCountsPerMillion'
        REGULATION = 'regulation'

    class Regulation(object):
        UP = 'up'
        DOWN = 'down'

    def __init__(self):
        """
        Create a new genome query.
        The default parameters for a query are:

            - offset = 0
            - limit = 5000
            - no filters
            - search across all contrasts
            - sorting by increasing FDR

        :rtype: GenomeQuery
        """
        self._map = {'filter': {}}

    def set_feature_ids(self, features):
        features = features if isinstance(features, list) else [features]
        self._map['featureId'] = self._DELIMITER.join(features)
        return self

    def set_offset(self, offset):
        self._map['offset'] = offset
        return self

    def set_limit(self, limit):
        """
        Set maximum number of entries to retrieve **per contrast**.

        :param limit:
        :return:
        """
        self._map['limit'] = limit
        return self

    def set_order_ascending(self, ascending):
        self._map['ascending'] = ascending
        return self

    def set_contrasts(self, contrasts):
        contrasts = contrasts if isinstance(contrasts, list) else [contrasts]
        self._map['contrastLevel'] = self._DELIMITER.join(contrasts)
        return self

    def set_sorting_order(self, order):
        self._map['sortingOrder'] = order
        return self

    def add_filter(self, key, value):
        self._map['filter'][key] = str(value)

    def get_map(self):
        return self._map.copy()
