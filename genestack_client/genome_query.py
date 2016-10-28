
class GenomeQuery(object):

    class SortingOrder(object):
        BY_P_VALUE = 'ByPValue'

    def __init__(self):
        self._map = {}

    def set_feature_ids(self, features):
        features = features if isinstance(features, list) else [features]
        self._map['featureId'] = '|'.join(features)
        return self

    def set_offset(self, offset):
        self._map['offset'] = offset
        return self

    def set_limit(self, limit):
        self._map['limit'] = limit
        return self

    def set_order_ascending(self, ascending):
        self._map['ascending'] = ascending
        return self

    def set_contrast(self, contrast):
        self._map['contrastLevel'] = contrast
        return self

    def set_sorting_order(self, order):
        self._map['sortingOrder'] = order
        return self

    def get_map(self):
        return self._map.copy()