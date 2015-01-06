
from . import fields
from .exceptions import ValidationError
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
