
class ModelRecordSet():
    """
    Encapsulates the results of a find() on a Model
    """
    def __init__(self, model):
        self._model = model
    def __len__(self):
        raise Exception('ModelRecordSet object should implement __len__()')
    def __getitem__(self, key):
        raise Exception('ModelRecordSet object should implement __getitem__()')
    def __iter__(self):
        raise Exception('ModelRecordSet object should implement __iter__()')
    def __next__(self):
        raise Exception('ModelRecordSet object should implement __next__()')

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self._model)

    def to_json(self):
        return [record.to_json() for record in self]

class ModelRecord():
    """
    Encapsulates a single database record, normally returned from a ModelRecordSet
    """
    def __init__(self, model):
        self._model = model
        
    def __getitem__(self, key):
        raise Exception('ModelRecord object should implement __getitem__()')

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self._model)

    def get(self, key, default=None):
        res = default
        try:
            res = self[key]
        except KeyError:
            pass
        return res

    @property
    def fields(self):
        """
        return the dictionary of fields for this record type
        """
        return self._model._fields
    
    def to_dict(self):
        res = {}
        for field in self.fields.keys():
            res[field] = self.get(field, None)
        return res
    
    def to_json(self):
        return str(self.to_dict())
