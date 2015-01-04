
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

class InMemoryRecordSet(ModelRecordSet):
    """
    Encapsulates the results of a find() on an InMemoryRecordSet
    """
    def __init__(self, model, records):
        super().__init__(model)
        self._records = records
        self._current_record_idx = 0
        
    def __len__(self):
        return len(self._records)

    def __getitem__(self, key):
        return InMemoryRecord(self._model, self._records[key])
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self._current_record_idx < len(self._records):
            item, \
            self._current_record_idx = \
                InMemoryRecord(self._model, self._records[self._current_record_idx]), \
                self._current_record_idx + 1
            return item
        else:
            raise StopIteration()

class InMemoryRecord(ModelRecord):
    """
    Encapsulates a single in-memory record, normally returned from an InMemoryRecordSet
    """
    def __init__(self, model, record):
        super().__init__(model)
        self._record = record
        
    def __getitem__(self, key):
        if key not in self._record:
            raise KeyError(key)
        return self._record[key]
