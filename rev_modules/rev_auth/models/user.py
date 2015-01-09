
from rev.db import Model, fields
from rev.i18n import translate as _

class User(Model):

    _description = 'User'
    
    id = fields.RecordIDField(_('User ID'))
    name = fields.TextField(_('Login Name'))
    email = fields.TextField(_('E-mail Address'))

    _unique = ['name']