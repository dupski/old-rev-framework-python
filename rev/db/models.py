
import re

from rev.models import Model, fields
from rev.models.exceptions import ValidationError, ModelNotFoundError

class DBModel(Model):
    
    def __init__(self, registry, db):
        
        super().__init__(registry)
        
        self._db = db
        
        # _table_name is CamelCaseName converted to camel_case_name
        self._table_name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', self._name)
        self._table_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', self._table_name).lower()
        self._table_name.replace('__', '_')
        
        # initialise model in database #TODO: This should really be done via syncdb
        self._db.init_model(self)
    
    def find(self, criteria={}, read_fields=[], order_by=None, limit=0, offset=0, count_only=False, context={}):
        """
        Search the database using the specified criteria, and return the matching data
        """
        
        return self._db.find(self, criteria, read_fields, order_by, limit, offset, count_only, context)
        
    def create(self, vals, context={}):
        """
        Creates a new record. Returns the id of the created record
        """

        create_vals = super().get_create_vals(vals, context)
        
        # Do Create
        id = self._db.create(self, create_vals, context)
        
        return id        

    def update(self, criteria, vals, limit=0, context={}):
        """
        Updates existing records. Returns True if successful
        """
                
        super().validate_field_values(vals)
        
        # Do Update
        res = self._db.update(self, criteria, vals, limit, context)
        
        return True
    
    def delete(self, criteria, limit=0, context={}):
        """
        Deletes existing records. Returns True if successful
        """
        
        # Do Delete
        res = self._db.delete(self, criteria, limit, context)
        
        return True