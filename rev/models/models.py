
from . import fields
from .exceptions import ValidationError
from .records import InMemoryRecordSet
from .fields import Field
from rev.i18n import translate as _

import logging

class Model():
    
    def __init__(self, registry):
        
        self._registry = registry
        self._name = self.__class__.__name__
        self._module = self.__class__.__module__
        
        if not self._description:
            raise Exception('Models must have a _description property defined!');

        logging.info('Loading Model: %s (%s)', self._name, self._description)
        
        # configure self._fields
        self._fields = {}
        for attr in dir(self):
            if isinstance(getattr(self, attr), Field):
                self._fields[attr] = getattr(self, attr)
    
    def find(self, criteria={}, read_fields=[], order_by=None, limit=0, offset=0, count_only=False, context={}):
        """
        Search the model data using the specified criteria, and return the matching data
        Returns a ModelRecords iterable object
        """
        raise Exception("find() not implemented for this Model type")

    def validate_field_values(self, vals):
        """
        Validates the provided field values against the RevFields defined on
        the object.
        
        Raises a rev.models.exceptions.ValidationError if there is a problem
        """
        
        extra_fields = set(vals.keys()) - set(self._fields.keys())
        
        if extra_fields != set():
            raise ValidationError("Object '{}' does not have the following fields: {}".format(self._name, ', '.join(extra_fields)))
        
        for field_name in vals:
            self._fields[field_name].validate_value(self, field_name, vals[field_name])
    
    def get_create_vals(self, vals, context={}):
        """
        Process and validate values for new records
        """
        create_vals = {}
        
        # Start from default values
        for fld, fld_obj in self._fields.items():
            create_vals[fld] = fld_obj.get_default_value()
        
        create_vals.update(vals)
        
        self.validate_field_values(create_vals)
        
        return create_vals
    
    def create(self, vals, context={}):
        """
        Creates a new record. Returns the id of the created record
        """
        raise Exception("create() not implemented for this Model type")

    def update(self, criteria, vals, limit=0, context={}):
        """
        Updates existing records. Returns True if successful
        """
        raise Exception("update() not implemented for this Model type")
    
    def delete(self, criteria, limit=0, context={}):
        """
        Deletes existing records. Returns True if successful
        """
        raise Exception("delete() not implemented for this Model type")


class InMemoryModel(Model):
    """
    A simple model that uses a dictionary for its storage. The dictionary is
    currently only keyed (and therefore searchable) by 'id'.
    """

    # InMemoryModels must have an 'id' (the dictionary key)
    id = fields.RecordIDField(_('Record ID'))
    
    def __init__(self, registry):
        super().__init__(registry)
        self._data = {}
    
    def find(self, criteria={}, read_fields=[], order_by=None, limit=0, offset=0, count_only=False, context={}):
        """
        Search the model data using the specified criteria, and return the matching data
        Returns a ModelRecords iterable object
        """
        if criteria == {}:
            return InMemoryRecordSet(self, [self._data[id] for id in self._data.keys()])

        # We currently only allow searching by id
        if 'id' not in criteria:
            raise ValidationError("InMemoryModel records can only be searched by 'id'")
        if isinstance(criteria['id'], str):
            if criteria['id'] in self._data:
                return InMemoryRecordSet(self, [self._data[criteria['id']]])
            else:
                return InMemoryRecordSet(self, [])
        else:
            return InMemoryRecordSet(self, [self._data[id] for id in criteria['id']['$in'] if id in self._data])
    
    def create_record_id(self, vals, context={}):
        """
        Generate a unique ID for the new record
        """
        from uuid import uuid4
        return str(uuid4())
    
    def create(self, vals, context={}):
        """
        Creates a new record. Returns the id of the created record
        """

        if 'id' not in vals:
            vals['id'] = self.create_record_id(vals, context)
        
        create_vals = super().get_create_vals(vals, context)
                
        if create_vals['id'] in self._data:
            raise ValidationError("The id '{}' already exists".format(create_vals['id']))
        
        # Do Create
        self._data[create_vals['id']] = create_vals
        
        return create_vals['id']        

    def update(self, criteria, vals, limit=0, context={}):
        """
        Updates existing records. Returns True if successful
        #TODO: Implement 'limit'
        """
                
        super().validate_field_values(vals)
        
        if 'id' not in criteria:
            raise ValidationError("InMemoryModel records can only be updated by 'id'")

        if isinstance(criteria['id'], str):
            self._data[criteria['id']].update(vals)
        else:
            for id in criteria['id']['$in']:
                self._data[id].update(vals)
        
        return True
    
    def delete(self, criteria, limit=0, context={}):
        """
        Deletes existing records. Returns True if successful
        #TODO: Implement 'limit'
        """

        if 'id' not in criteria:
            raise ValidationError("InMemoryModel records can only be deleted by 'id'")

        if isinstance(criteria['id'], str):
            del self._data[criteria['id']]
        else:
            for id in criteria['id']['$in']:
                del self._data[id]
            
        return True
