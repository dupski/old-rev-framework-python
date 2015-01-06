
class ModelRecordSet():
    """
    Subclasses should encapsulate the results of a model find() call and
    present them as a standard iterable
    """    
    def __init__(self, model):
        self._model = model
    def __iter__(self):
        raise Exception('__iter__() not implemented for this ModelRecordList type!')
    def __getitem__(self, key):
        raise Exception('__getitem__() not implemented for this ModelRecordList type!')
    def __len__(self):
        raise Exception('__len__() not implemented for this ModelRecordList type!')
    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self._model)

    def to_json(self):
        return [record.to_json() for record in self]

class ModelRecord():
    """
    Encapulates a single record
    """
    
    def __init__(self, model):
        self._model = model
    def __getitem__(self, key):
        raise Exception('__getitem__() not implemented for this ModelRecord type!')
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
