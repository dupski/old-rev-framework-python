
from rev.db.models import DBModel
from rev.models import fields
from rev.i18n import translate as _

class User(DBModel):

    _description = 'User'
    
    name = fields.TextField(_('Login Name'))
    email = fields.TextField(_('E-mail Address'))

    _unique = ['name']