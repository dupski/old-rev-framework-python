
import logging

from rev.db.exceptions import ValidationError
from rev.db import DBProvider
from rev.db.records import ModelRecordSet, ModelRecord

# DatbaseProvider that uses a Dictionary in the user's Session to store its data

class DatabaseProvider(DBProvider):
    
    def __init__(self, config, name):
        self.name = name
                
        logging.warning("Initialising Dict Storage InMemoryModelProvider - DO NOT USE IN PRODUCTION !")
        self._data = {}
        
    def init_model(self, model):
        # Create collection for specified model if it does not already exist
        
        logging.debug('Creating Cache for: %s', model._name)
        self._data[model._name] = {}
        
        if hasattr(model, '_unique'):
            logging.warning('Cannot create unique constraints on InMemoryModels!')
    
    def find(self, model, criteria={}, read_fields=[], order_by=None, limit=0, offset=0, count_only=False, context={}):
        """
        Search the model data using the specified criteria, and return the matching data
        Returns a ModelRecords iterable object
        """

        if criteria == {}:
            return SessionRecordSet(self, [self._data[model._name][id] for id in self._data.keys()])

        # We currently only allow searching by id
        if 'id' not in criteria:
            raise ValidationError("InMemoryModel records can only be searched by 'id'")
        if isinstance(criteria['id'], str):
            if criteria['id'] in self._data[model._name]:
                return SessionRecordSet(self, [self._data[model._name][criteria['id']]])
            else:
                return SessionRecordSet(self, [])
        else:
            return SessionRecordSet(self, [self._data[model._name][id] for id in criteria['id']['$in'] if id in self._data[model._name]])        

    def create_record_id(self, model, vals, context={}):
        """
        Generate a unique ID for the new record
        """
        from uuid import uuid4
        return str(uuid4())
    
    def create(self, model, vals, context={}):
        """
        Creates a new record. Returns the id of the created record
        """
                        
        if vals['id'] in self._data[model._name]:
            raise ValidationError("The id '{}' already exists".format(vals['id']))
        
        # Do Create
        self._data[model._name][vals['id']] = vals
        
        return vals['id']        

    def update(self, model, criteria, vals, limit=0, context={}):
        """
        Updates existing records. Returns True if successful
        #TODO: Implement 'limit'
        """
        
        if isinstance(criteria['id'], str):
            self._data[model._name][criteria['id']].update(vals)
        else:
            for id in criteria['id']['$in']:
                self._data[model._name][id].update(vals)
        
        return True
    
    def delete(self, model, criteria, limit=0, context={}):
        """
        Deletes existing records. Returns True if successful
        #TODO: Implement 'limit'
        """

        if 'id' not in criteria:
            raise ValidationError("InMemoryModel records can only be deleted by 'id'")

        if isinstance(criteria['id'], str):
            del self._data[model._name][criteria['id']]
        else:
            for id in criteria['id']['$in']:
                del self._data[model._name][id]
            
        return True


class SessionRecordSet(ModelRecordSet):
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
        return SessionRecord(self._model, self._records[key])
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self._current_record_idx < len(self._records):
            item, \
            self._current_record_idx = \
                SessionRecord(self._model, self._records[self._current_record_idx]), \
                self._current_record_idx + 1
            return item
        else:
            raise StopIteration()

class SessionRecord(ModelRecord):
    """
    Encapsulates a single in-memory record, normally returned from an InMemoryRecordSet
    """
    def __init__(self, model, record):
        super().__init__(model)
        self._record = record
        
    def __getitem__(self, key):
        if key not in self.fields.keys():
            raise KeyError(key)
        return self._record.get(key, None)
