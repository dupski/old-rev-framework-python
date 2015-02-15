
from .exceptions import ValidationError

class Field():
    
    def __init__(self, label, **kwargs):
        self.label = label
        self.required = kwargs.get('required', True)
        self.readonly = kwargs.get('readonly', False)
        self.default_value = kwargs.get('default_value', None)
    
    def get_default_value(self):
        return self.default_value
    
    def validate_value(self, obj, name, value):
        if name != 'id' and self.required and not value:
            raise ValidationError("Field '{}' on object '{}' is required!".format(name, obj._name))

# Primary Key Field

class RecordIDField(Field):
    pass

# Plain Value Fields

class TextField(Field):
    def __init__(self, label, multiline=False, **kwargs):
        super().__init__(label, **kwargs)
        self.multiline = multiline

class EmailAddressField(TextField):
    def __init__(self, label, **kwargs):
        super().__init__(label, **kwargs)
        self.multiline = False

class PhoneNumberField(TextField):
    def __init__(self, label, **kwargs):
        super().__init__(label, **kwargs)
        self.multiline = False

class URLField(TextField):
    def __init__(self, label, **kwargs):
        super().__init__(label, **kwargs)
        self.multiline = False

class PasswordField(TextField):
    def __init__(self, label, **kwargs):
        super().__init__(label, **kwargs)
        self.multiline = False

class SelectionField(Field):
    def __init__(self, label, selection, **kwargs):
        super().__init__(label, **kwargs)
        self.selection = selection

class MultiSelectionField(Field):

    def __init__(self, label, selection, **kwargs):
        super().__init__(label, **kwargs)
        self.selection = kwargs.get('selection', [])
    
    def validate_value(self, obj, name, value):
        if not isinstance(value, list):
            raise ValidationError("Invalid value for multi-select field '{}' of object '{}'!".format(name, obj._name))

class IntegerField(Field):
    pass

class FloatField(Field):
    pass

class DecimalField(Field):
    pass

class BooleanField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.default_value:
            self.default_value = True
        else:
            self.default_value = False

class DateField(Field):
    pass

class DateTimeField(Field):
    pass

# Data Fielda

class JSONField(Field):
    pass

# Relational Fields

class RecordLinkField(Field):
    """
    Stores links to one or more related records
    
    Use the 'multi' keyword argument to allow linking to multiple records
    """
    def __init__(self, label, related_model, **kwargs):
        super().__init__(label, **kwargs)
        self.related_model = related_model
        self.multi = kwargs.get('multi', False)

class RecordListField(Field):
    """
    Returns a list of related records
    """
    def __init__(self, label, related_model, filter, **kwargs):
        super().__init__(label, **kwargs)
        self.related_model = related_model
        self.filter = filter
