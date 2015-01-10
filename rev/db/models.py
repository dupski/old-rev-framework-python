
import logging

from rev.db import fields
from rev.db.exceptions import ValidationError

class Model():
    
    def __init__(self, registry, *args, **kwargs):

        if not getattr(self, '_description', False):
            raise Exception('Models must have a _description property defined!');

        if not getattr(self, '_database', False):
            self._database = 'default'
        
        self._name = self.__class__.__name__
        self._module = self.__class__.__module__
        self._registry = registry
        self._database = registry.app.databases[self._database]

        logging.debug('Loading Model: %s (%s)', self._name, self._description)
        
        # configure self._fields
        self._fields = {}
        for attr in dir(self):
            if isinstance(getattr(self, attr), fields.Field):
                self._fields[attr] = getattr(self, attr)
        
        # initialise model in database #TODO: This should really be done via syncdb
        self._database.init_model(self)
        
        # Make sure any mixin classes are also __init__'ed
        super().__init__(*args, **kwargs)
    
    def find(self, criteria={}, read_fields=['*'], order_by=None, limit=0, offset=0, count_only=False, context={}):
        """
        Search the database using the specified criteria, and return the matching data
        """
        
        return self._database.find(self, criteria, read_fields, order_by, limit, offset, count_only, context)

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

    def create(self, vals, context={}):
        """
        Creates a new record. Returns the id of the created record
        """

        create_vals = self.get_create_vals(vals, context)
        
        # Do Create
        id = self._database.create(self, create_vals, context)
        
        return id        

    def update(self, criteria, vals, limit=0, context={}):
        """
        Updates existing records. Returns True if successful
        """
                
        self.validate_field_values(vals)
        
        # Do Update
        res = self._database.update(self, criteria, vals, limit, context)
        
        return True
    
    def delete(self, criteria, limit=0, context={}):
        """
        Deletes existing records. Returns True if successful
        """
        
        # Do Delete
        res = self._database.delete(self, criteria, limit, context)
        
        return True