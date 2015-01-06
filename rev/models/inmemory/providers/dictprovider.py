
import logging

from rev.models.exceptions import ValidationError
from rev.models.inmemory.provider import InMemoryModelProvider
from rev.models.inmemory.records import InMemoryRecordSet


# InMemoryProvider that uses a Dictionary (per process, so no good for production!)

class InMemoryProvider(InMemoryModelProvider):
    
    def __init__(self, config):
                
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
            return InMemoryRecordSet(self, [self._data[model._name][id] for id in self._data.keys()])

        # We currently only allow searching by id
        if 'id' not in criteria:
            raise ValidationError("InMemoryModel records can only be searched by 'id'")
        if isinstance(criteria['id'], str):
            if criteria['id'] in self._data[model._name]:
                return InMemoryRecordSet(self, [self._data[model._name][criteria['id']]])
            else:
                return InMemoryRecordSet(self, [])
        else:
            return InMemoryRecordSet(self, [self._data[model._name][id] for id in criteria['id']['$in'] if id in self._data[model._name]])        

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
