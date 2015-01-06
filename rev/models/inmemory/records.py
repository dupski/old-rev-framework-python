
from rev.models.records import ModelRecordSet, ModelRecord 

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
