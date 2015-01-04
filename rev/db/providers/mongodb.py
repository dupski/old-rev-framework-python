
import logging

from rev.db import DBProvider
from rev.db.records import DBModelRecordSet
import pymongo
from bson.objectid import ObjectId
from copy import deepcopy

ORDER_BY_OPTIONS = {
    'asc' : pymongo.ASCENDING,
    'desc' : pymongo.DESCENDING,
}

# Mongo DB Database Provider

class DatabaseProvider(DBProvider):
    
    def __init__(self, db_config):
        # Initialise database including recording settings from app.settings
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
            return DBModelRecordSet(model, res)
        
    def create(self, model, vals, context={}):
        """
        Creates a new record. Returns the id of the created record
        """
        
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
