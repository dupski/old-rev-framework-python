
from rev.core import models, fields
from rev.core.translations import translate as _

class RevActionType(models.RevModel):

    _description = 'Rev App UI Action Type'
    
    name = fields.TextField(_('Action Name'))
    home_action = fields.RecordLinkField(_('Home Action'), 'RevAction')

    _unique = ['name']

class RevAction(models.RevModel):

    _description = 'Rev App UI Action'
    
    module = fields.TextField(_('Module Name'))
    name = fields.TextField(_('Action Name'))
    type = fields.RecordLinkField(_('Action Type'), 'RevActionType')
    views = fields.RecordLinkField(_('Associated Views'), 'RevView', multi=True)
    context = fields.TextField(_('Action Context'), required=False)
    filter = fields.TextField(_('Action Data Filter'), required=False)

    _unique = [('module', 'name')]