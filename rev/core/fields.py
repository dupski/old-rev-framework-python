
from rev.core.exceptions import ValidationError

class RevField():
    
    def __init__(self, label, **kwargs):
        self.label = label
        self.required = kwargs.get('required', True)
        self.readonly = kwargs.get('readonly', False)
        self.default_value = kwargs.get('default_value', None)
    
    def get_default_value(self):
        return self.default_value
    
    def validate_value(self, obj, name, value):
        if self.required and not value:
            raise ValidationError("Field '{}' on object '{}' is required!".format(name, obj._name))

class TextField(RevField):
    pass

class SelectionField(RevField):
    def __init__(self, *args, **kwargs):
        super(SelectionField, self).__init__(*args, **kwargs)
        self.selection = kwargs.get('selection', [])

class MultiSelectionField(RevField):

    def __init__(self, *args, **kwargs):
        super(MultiSelectionField, self).__init__(*args, **kwargs)
        self.selection = kwargs.get('selection', [])
    
    def validate_value(self, obj, name, value):
        if not isinstance(value, list):
            raise ValidationError("Invalid value for multi-select field '{}' of object '{}'!".format(name, obj._name))

class IntegerField(RevField):
    pass

class FloatField(RevField):
    pass

class DecimalField(RevField):
    pass

class BooleanField(RevField):
    def __init__(self, *args, **kwargs):
        super(BooleanField, self).__init__(*args, **kwargs)
        if self.default_value:
            self.default_value = True
        else:
            self.default_value = False

class DateField(RevField):
    pass

class DateTimeField(RevField):
    pass
