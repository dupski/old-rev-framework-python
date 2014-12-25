
from rev.db import models, fields
from rev.i18n import translate as _

class RevUser(models.RevModel):

    _description = 'User'
    
    name = fields.TextField(_('Login Name'))
    email = fields.TextField(_('E-mail Address'))

    _unique = ['name']