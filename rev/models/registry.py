
from .exceptions import ModelNotFoundError

class ModelRegistry():
    """
    Generic Model Registry that facilitates communication and overriding of models
    """
    
    def __init__(self, app):
        
        self.app = app
        self._models = {}
    
    def set(self, model_name, instance):
        self._models[model_name] = instance
    
    def get(self, model_name):
        if (model_name not in self._models):
            raise ModelNotFoundError("Model '{}' does not exist!".format(model_name))
        else:
            return self._models[model_name]

    def model_exists(self, model_name):
        return True if model_name in self._models else False
    
    def validate(self):
        pass # TODO: Validate model registry, checking referential integrity, etc.