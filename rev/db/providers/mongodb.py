
import logging

from rev.db import DBProvider
from rev.db.records import ModelRecordSet, ModelRecord
import pymongo
from bson.objectid import ObjectId
from copy import deepcopy

import re

ORDER_BY_OPTIONS = {
    'asc' : pymongo.ASCENDING,
    'desc' : pymongo.DESCENDING,
}

# Mongo DB Database Provider

class DatabaseProvider(DBProvider):
    
    def __init__(self, db_config, name):
        # Initialise database provider including recording settings from app.config
        self.name = name
        self.host = db_config['host']
        self.port = db_config['port']
        self.db_name = db_config['database']
        
        # Connect to Database
        logging.info("Database Server: {}:{}".format(self.host, self.port))
        logging.info("Database Name: {}".format(self.db_name))

        self._dbclient = pymongo.MongoClient(self.host, self.port)
        self._db = self._dbclient[self.db_name]
        
    def init_model(self, model):
        # Create collection for specified model if it does not already exist
        
        db = self._db

        # _table_name is CamelCaseName converted to camel_case_name
        model._table_name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', model._name)
        model._table_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', model._table_name).lower()
        model._table_name.replace('__', '_')
        
        if model._table_name not in db.collection_names():
            logging.info('Creating Collection: %s', model._table_name)
            db.create_collection(model._table_name)
        
        if hasattr(model, '_unique'):
            for unq_key in model._unique:
                if unq_key:
                    logging.debug('Ensuring Unique Constraint for: %s', unq_key)
                    if isinstance(unq_key, str):
                        db[model._table_name].ensure_index(unq_key, unique=True )
                    elif isinstance(unq_key, (list, tuple)):
                        index_spec = []
                        for unq_field in unq_key:
                            index_spec.append((unq_field, pymongo.ASCENDING))
                        db[model._table_name].ensure_index(index_spec, unique=True )

    
    def find(self, model, criteria={}, read_fields=[], order_by=None, limit=0, offset=0, count_only=False, context={}):
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
        
        db = self._db
        cr = db[model._table_name].find(spec=criteria, fields=read_fields, sort=order_by, limit=limit, skip=offset)
        
        if count_only:
            return cr.count()
        else:
            res = []
            for rec in cr:
                if rec['_id']:
                    rec['id'] = str(rec['_id'])
                    del rec['_id']
                res.append(rec)
            return MongoDBRecordSet(model, res)
        
    def create(self, model, vals, context={}):
        """
        Creates a new record. Returns the id of the created record
        """
        
        if 'id' in vals:
            del vals['id'] # Temporary workaround until we figure out a good way to handle mongo's _id
            
        id = self._db[model._table_name].insert(vals)
        return id        

    def update(self, model, criteria, vals, limit=0, context={}):
        """
        Updates existing records. Returns True if successful
        TODO: Implement 'limit'
        """
        
        if 'id' in criteria:
            criteria = deepcopy(criteria)
            if isinstance(criteria['id'], str):
                criteria['_id'] = ObjectId(criteria['id'])
                del criteria['id']
            else:
                criteria['_id'] = {'$in' : [ObjectId(id) for id in criteria['id']['$in']]}
                del criteria['id']
        
        res = self._db[model._table_name].update(criteria, {'$set' : vals}, multi=True)
        
        return True
    
    def delete(self, model, criteria, limit=0, context={}):
        """
        Deletes existing records. Returns True if successful
        TODO: Implement 'limit'
        """

        if 'id' in criteria:
            criteria = deepcopy(criteria)
            if isinstance(criteria['id'], str):
                criteria['_id'] = ObjectId(criteria['id'])
                del criteria['id']
            else:
                criteria['_id'] = {'$in' : [ObjectId(id) for id in criteria['id']['$in']]}
                del criteria['id']
        
        res = self._db[model._table_name].remove(criteria, multi=True)


class MongoDBRecordSet(ModelRecordSet):
    """
    Encapsulates the results of a find() on a Model from MongoDB
    Currently this simply re-returns the list of results, however in future
    this could be extended to make use of cursors
    """
    def __init__(self, model, records):
        super().__init__(model)
        self._records = records
        self._current_record_idx = 0
        
    def __len__(self):
        return len(self._records)

    def __getitem__(self, key):
        return MongoDBRecord(self._model, self._records[key])
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self._current_record_idx < len(self._records):
            item, \
            self._current_record_idx = \
                MongoDBRecord(self._model, self._records[self._current_record_idx]), \
                self._current_record_idx + 1
            return item
        else:
            raise StopIteration()


class MongoDBRecord(ModelRecord):
    """
    Encapsulates a single database record, normally returned from a ModelRecordSet
    """
    def __init__(self, model, record):
        super().__init__(model)
        self._record = record
        
    def __getitem__(self, key):
        if key not in self.fields.keys():
            raise KeyError(key)
        return self._record.get(key, None)
