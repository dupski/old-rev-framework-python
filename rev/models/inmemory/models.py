
from rev.models import Model, fields
from rev.models.exceptions import ValidationError
from rev.i18n import translate as _

class InMemoryModel(Model):
    """
    A simple model that uses a dictionary for its storage. The dictionary is
    currently only keyed (and therefore searchable) by 'id'.
    """

    # InMemoryModels must have an 'id' (the dictionary key)
    id = fields.RecordIDField(_('Record ID'))
    
    def __init__(self, registry, provider):
        super().__init__(registry)
        self._provider = provider
        self._provider.init_model(self)
            
    def find(self, criteria={}, read_fields=[], order_by=None, limit=0, offset=0, count_only=False, context={}):
        """
        Search the model data using the specified criteria, and return the matching data
        Returns a ModelRecords iterable object
        """
        return self._provider.find(self, criteria, read_fields, order_by, limit, offset, count_only, context)
    
    def create_record_id(self, vals, context={}):
        """
        Generate a unique ID for the new record
        """
        return self._provider.create_record_id(self, vals, context)
    
    def create(self, vals, context={}):
        """
        Creates a new record. Returns the id of the created record
        """
        
        if 'id' not in vals:
            vals['id'] = self.create_record_id(vals, context)
        
        create_vals = super().get_create_vals(vals, context)

        return self._provider.create(self, create_vals, context)

    def update(self, criteria, vals, limit=0, context={}):
        """
        Updates existing records. Returns True if successful
        """
                
        super().validate_field_values(vals)
        
        if 'id' not in criteria:
            raise ValidationError("InMemoryModel records can only be updated by 'id'")
        
        return self._provider.update(self, criteria, limit, context)
    
    def delete(self, criteria, limit=0, context={}):
        """
        Deletes existing records. Returns True if successful
        """

        if 'id' not in criteria:
            raise ValidationError("InMemoryModel records can only be deleted by 'id'")
            
        return self._provider.delete(self, criteria, limit, context)
