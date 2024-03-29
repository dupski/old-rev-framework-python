

class DBProvider():
    """
    Base Class for Rev DB Providers
    """
    
    def __init__(self, db_config, name):
        # Initialise database including recording settings from app.config
        pass
        
    def init_model(self, model):
        # Create database table or collection for specified model
        pass
    
    def find(self, model, criteria={}, read_fields='*', order_by=None, limit=0, offset=0, count_only=False, context={}):
        raise NotImplementedError("Provider does not implement the find() method.")
        
    def create(self, model, vals, context={}):
        raise NotImplementedError("Provider does not implement the create() method.")
    
    def update(self, model, critria, vals, limit=0, context={}):
        raise NotImplementedError("Provider does not implement the update() method.")
    
    def delete(self, model, criteria, limit=0, context={}):
        raise NotImplementedError("Provider does not implement the delete() method.")
