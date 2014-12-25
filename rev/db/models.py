
import re

from rev.db.fields import RevField
from rev.db.exceptions import ValidationError, ModelNotFoundError

import logging

class RevModelRegistry():
    
    def __init__(self, app, db):
        
        self.app = app
        self.db = db
        self._models = {}
    
    def set(self, model_name, instance):
        self._models[model_name] = instance
    
    def get(self, model_name):
        if (model_name not in self._models):
            raise ModelNotFoundError("Model '{}' does not exist!".format(model_name))
        else:
            return self._models[model_name]

    def model_exists(self, model_name):
        return True if model_name in self._models else False
    
    def validate(self):
        pass # TODO: Validate model registry, checking referential integrity, etc.

class RevModel():
    
    def __init__(self, registry):
        
        self.registry = registry
        
        self._name = self.__class__.__name__
        self._module = self.__class__.__module__
        
        if not self._description:
            raise Exception('Rev Models must have a _description properties defined!');

        logging.info('Loading Model: %s (%s)', self._name, self._description)
    
        self.registry = registry
        
        # _table_name is CamelCaseName converted to camel_case_name
        self._table_name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', self._name)
        self._table_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', self._table_name).lower()
        self._table_name.replace('__', '_')
        
        # configure self._fields
        self._fields = {}
        for attr in dir(self):
            if isinstance(getattr(self, attr), RevField):
                self._fields[attr] = getattr(self, attr)
        
        # initialise model in database #TODO: This should really be done via syncdb
        self.registry.db.init_model(self)
    
    def find(self, criteria={}, read_fields=[], order_by=None, limit=0, offset=0, count_only=False, context={}):
        """
        Search the database using the specified criteria, and return the matching data
        """
        
        db = self.registry.db
        return db.find(self, criteria, read_fields, order_by, limit, offset, count_only, context)
    
    def validate_field_values(self, vals):
        """
        Validates the provided field values against the RevFields defined on
        the object.
        
        Raises a rev.core.exceptions.ValidationError if there is a problem
        """
        
        extra_fields = set(vals.keys()) - set(self._fields.keys())
        
        if extra_fields != set():
            raise ValidationError("Object '{}' does not have the following fields: {}".format(self._name, ', '.join(extra_fields)))
        
        for field_name in vals:
            self._fields[field_name].validate_value(self, field_name, vals[field_name])
    
    def create(self, vals, context={}):
        """
        Creates a new record. Returns the id of the created record
        """

        create_vals = {}
        
        # Start from default values
        for fld, fld_obj in self._fields.items():
            create_vals[fld] = fld_obj.get_default_value()
        
        create_vals.update(vals)
        
        self.validate_field_values(create_vals)
        
        # Do Create
        db = self.registry.db
        id = db.create(self, create_vals, context)
        
        return id        

    def update(self, ids, vals, context={}):
        """
        Updates existing records. Returns True if successful
        """
                
        self.validate_field_values(vals)
        
        # Do Update
        db = self.registry.db
        res = db.update(self, ids, vals, context)
        
        return True
    
    def delete(self, ids, context={}):
        """
        Deletes existing records. Returns True if successful
        """
        
        # Do Delete
        db = self.registry.db
        res = db.delete(self, id_list, context)
        
        return True