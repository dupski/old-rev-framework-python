
import re
import rev
from rev.core.fields import RevField
from rev.core.exceptions import ValidationError

import pymongo
from bson.objectid import ObjectId

ORDER_BY_OPTIONS = {
    'asc' : pymongo.ASCENDING,
    'desc' : pymongo.DESCENDING,
}

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
        
        self._name = self.__class__.__name__
        self._module = self.__class__.__module__
        
        if not self._description:
            raise Exception('Rev Models must have a _description properties defined!');

        rev.log.info('Loading Model: %s (%s)', self._name, self._description)
    
        self.registry = registry
        
        # _table_name is CamelCaseName converted to camel_case_name
        self._table_name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', self._name)
        self._table_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', self._table_name).lower()
        self._table_name.replace('__', '_')
        
        self._fields = {}
        for attr in dir(self):
            if isinstance(getattr(self, attr), RevField):
                self._fields[attr] = getattr(self, attr)
        
        if self._table_name not in db.collection_names():
            rev.log.info('Creating Collection: %s', self._table_name)
            db.create_collection(self._table_name)
        
        if hasattr(self, '_unique'):
            for unq_key in self._unique:
                # TODO: Support compound keys
                if isinstance(unq_key, str):
                    rev.log.debug('Ensuring Unique Constraint for: %s', unq_key)
                    db[self._table_name].ensure_index(unq_key, unique=True )
    
    def find(self, criteria={}, read_fields=[], order_by=None, limit=0, offset=0, count_only=False, context={}):
        """
        Search the database using the specified criteria, and return the matching data
        """

        if 'id' in criteria:
            # replace 'id' with '_id' and also convert the string values to BSON ObjectIds
            if isinstance(criteria['id'], str):
                criteria['_id'] = ObjectId(criteria['id'])
            elif isinstance(criteria['id'], dict) and isinstance(criteria['id'].get('$in'), list):
                criteria['_id'] = {'$in' : [ObjectId(x) for x in criteria['id']['$in']]}

            del criteria['id']
        
        if count_only:
            read_fields = []
            order_by = None
            limit = None
            offset = None
        else:
            if read_fields == '*':
                # Make sure we read all fields then
                read_fields = None
            if order_by:
                # Replace asc / desc with db value
                for ob_key, ob_val in enumerate(order_by):
                    ob_val[1] = ORDER_BY_OPTIONS[ob_val[1]]
        
        db = self.registry.db
        cr = db[self._table_name].find(spec=criteria, fields=read_fields, sort=order_by, limit=limit, skip=offset)
        
        if count_only:
            return cr.count()
        else:
            res = []
            for rec in cr:
                if rec['_id']:
                    rec['id'] = str(rec['_id'])
                    del rec['_id']
                #TODO: Process function fields, etc.
                res.append(rec)
            return res
    
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
        id = db[self._table_name].insert(create_vals)
        
        return id        

    def update(self, ids, vals, context={}):
        """
        Updates existing records. Returns True if successful
        """
                
        self.validate_field_values(vals)

        id_list = []
        for id in ids:
            id_list.append(ObjectId(id))
        
        # Do Update
        db = self.registry.db
        res = db[self._table_name].update({'_id' : {'$in' : id_list}}, {'$set' : vals}, multi=True)
        
        return True
    
    def delete(self, ids, context={}):
        """
        Deletes existing records. Returns True if successful
        """

        id_list = []
        for id in ids:
            id_list.append(ObjectId(id))
        
        # Do Delete
        db = self.registry.db
        res = db[self._table_name].remove({'_id' : {'$in' : id_list}}, multi=True)