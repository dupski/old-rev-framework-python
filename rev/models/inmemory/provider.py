

class InMemoryModelProvider():
    """
    Base Class for Rev InMemoryModel Providers
    """
    
    def __init__(self, config):
        # Initialise provider using settings from app.settings
        pass
        
    def init_model(self, model):
        # Perform any initialisation needed for the specified model
        pass
    
    def find(self, model, criteria={}, read_fields=[], order_by=None, limit=0, offset=0, count_only=False, context={}):
        raise NotImplementedError("Provider does not implement the find() method.")
        
    def create(self, model, vals, context={}):
        raise NotImplementedError("Provider does not implement the create() method.")
    
    def update(self, model, critria, vals, limit=0, context={}):
        raise NotImplementedError("Provider does not implement the update() method.")
    
    def delete(self, model, criteria, limit=0, context={}):
        raise NotImplementedError("Provider does not implement the delete() method.")
