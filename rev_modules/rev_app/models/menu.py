
from . import MetadataModel
from rev.models import fields
from rev.i18n import translate as _

class Menu(MetadataModel):

    _description = 'Rev App UI Menu'
    
    name = fields.TextField(_('Menu Name'))
    parent = fields.RecordLinkField(_('Parent Menu'), 'Menu', required=False)
    action = fields.RecordLinkField(_('Action'), 'Action', required=False)
    icon = fields.TextField(_('Menu Icon'), required=False)
    sequence = fields.IntegerField(_('Menu Sequence'))
