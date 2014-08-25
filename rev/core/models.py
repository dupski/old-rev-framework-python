
import re
import rev

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
    
        self.registry = registry
        self._table_name = re.sub('[^A-Za-z0-9]+', '_', self._name).lower()

        rev.log.info('Loading model %s (%s)', self._name, self._description)
        
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

    def find(self, spec={}, read_fields=[], limit=80, count_only=False):
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