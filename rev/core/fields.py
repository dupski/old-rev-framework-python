
class RevField():
    def __init__(self, label, **kwargs):
        self.label = label
        self.required = kwargs.get('required', True)
        self.readonly = kwargs.get('readonly', False)

class TextField(RevField):
    pass

class SelectionField(RevField):
    def __init__(self, *args, **kwargs):
        super(SelectionField, self).__init__(*args, **kwargs)
        self.selection = kwargs.get('selection', [])

class IntegerField(RevField):
    pass

class FloatField(RevField):
    pass

class DecimalField(RevField):
    pass

class BooleanField(RevField):
    pass

class DateField(RevField):
    pass

class DateTimeField(RevField):
    pass
