
import re
import rev
from rev.core.fields import RevField
from rev.core.exceptions import ValidationException

from bson.objectid import ObjectId

class RevModelRegistry():
    
    def __init__(self, db):
        
        self.db = db
        self._models = {}
    
    def set(self, model_name, instance):
        self._models[model_name] = instance
    
    def get(self, model_name):
        if (model_name not in self._models):
            raise Exception("Model '{}' does not exist!".format(model_name))
        else:
            return self._models[model_name]
    
    def validate(self):
        pass # TODO: Validate model registry, checking referential integrity, etc.

class RevModel():
    
    def __init__(self, registry):
        
        db = registry.db
        
        if not self._name or not self._description:
            raise Exception('Rev Models must have _name and _description properties defined!');

        rev.log.info('Loading model %s (%s)', self._name, self._description)
    
        self.registry = registry
        self._table_name = re.sub('[^A-Za-z0-9]+', '_', self._name).lower()
        
        self._fields = {}
        for attr in dir(self):
            if isinstance(getattr(self, attr), RevField):
                self._fields[attr] = getattr(self, attr)
        
        if self._table_name not in db.collection_names():
            rev.log.info('Creating Collection %s', self._table_name)
            db.create_collection(self._table_name)
        
        if hasattr(self, '_unique'):
            for unq_key in self._unique:
                # TODO: Support compound keys
                if isinstance(unq_key, str):
                    rev.log.debug('Ensuring Unique constraint for %s', unq_key)
                    db[self._table_name].ensure_index(unq_key, unique=True )
                
    def post_init(self):
        pass # Hook to run after validation and before application start

    def find(self, spec={}, read_fields=[], limit=80, count_only=False, context={}):
        if not read_fields:
            # Make sure we read all fields then
            read_fields = None
        db = self.registry.db
        cr = db[self._table_name].find(spec=spec, fields=read_fields, limit=limit)
        if count_only:
            return cr.count()
        else:
            res = [x for x in cr]
            return res
    
    def validate_field_values(self, vals):
        """
        Validates the provided field values against the RevFields defined on
        the object.
        
        Raises a rev.core.exceptions.ValidationException if there is a problem
        """
        
        extra_fields = set(vals.keys()) - set(self._fields.keys())
        
        if extra_fields != set():
            raise ValidationException("Object '{}' does not have the following fields: {}".format(self._name, ', '.join(extra_fields)))
        
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
        id = db[self._table_name].insert(create_vals)
        
        return id        

    def update(self, id, vals, context={}):
        """
        Updates an existing record. Returns True if successful
        """
                
        self.validate_field_values(vals)
        
        id = ObjectId(id)
        
        # Do Update
        db = self.registry.db
        res = db[self._table_name].update({'_id' : id}, {'$set' : vals})
        
        return True

    def update_multiple(self, id_list, vals, context={}):
        """
        Updates multiple existing records. Returns True if successful
        """
                
        self.validate_field_values(vals)
        
        id_list = [ObjectId(id) for id in id_list]
        
        # Do Update
        db = self.registry.db
        res = db[self._table_name].update({'_id' : {'$in' : id_list}}, {'$set' : vals}, multi=True)
        
        return True