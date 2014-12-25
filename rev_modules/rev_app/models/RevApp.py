
from rev.db import models, fields
from rev.i18n import translate as _

class RevApp(models.RevModel):

    _description = 'Rev Application'
    
    name = fields.TextField(_('App Name'))
    home_action = fields.RecordLinkField(_('Home Action'), 'RevAction')

    _unique = ['name']