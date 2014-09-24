
from rev.core import models, fields
from rev.core.translations import translate as _

class RevMenu(models.RevModel):

    _description = 'Rev App UI Menu'
    
    name = fields.TextField(_('Menu Name'))
    parent = fields.RecordLinkField(_('Parent Menu'), 'RevMenu')
    action = fields.RecordLinkField(_('Action'), 'RevAction', required=False)
    icon = fields.TextField(_('Menu Icon'), required=False)
    sequence = fields.IntegerField(_('Menu Sequence'))
