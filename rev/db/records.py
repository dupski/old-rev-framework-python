
class ModelRecordSet():
    """
    Encapsulates the results of a find() on a Model
    DatabaseProviders must subclass this and return it from a find() call
    """
    def __init__(self, model, read_fields='*'):
        self.model = model
        self.read_fields = read_fields
    def __len__(self):
        raise Exception('ModelRecordSet object should implement __len__()')
    def __getitem__(self, item):
        raise Exception('ModelRecordSet object should implement __getitem__()')
    def __iter__(self):
        raise Exception('ModelRecordSet object should implement __iter__()')
    def __next__(self):
        raise Exception('ModelRecordSet object should implement __next__()')

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.model)

    def to_list(self):
        return [record.to_dict() for record in self]

    def to_json(self):
        return str(self.to_list())

class ModelRecord():
    """
    Encapsulates a single database record, normally returned from a ModelRecordSet
    """
    def __init__(self, model, read_fields='*', record={}):
        self.model = model
        self.read_fields = read_fields
        self.record = record
        
    def __getitem__(self, item):
        if self.read_fields == '*':
            if item not in self.model._fields.keys():
                raise Exception("Field '{}' does not exist in model '{}'".format(item, self.model))
            return self.record[item]
        else:
            if item not in self.read_fields:
                #TODO: Implement additional automatic lookups for non-read fields
                raise Exception("Field '{}' was not read as part of your find() call.".format(item))
            else:
                return self.record[item]

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.model)
    
    def __contains__(self, item):
        if self.read_fields == '*':
            return (item in self.model._fields.keys())
        else:
            return (item in self.read_fields)
    
    def to_dict(self):
        res = {}
        fields = self.model._fields.keys() if self.read_fields == '*' else self.read_fields
        for field in fields:
            res[field] = self.record.get(field, None)
        return res
    
    def to_json(self):
        return str(self.to_dict())
