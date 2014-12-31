
from rev.db import models, fields
from rev.i18n import translate as _

ACTION_TYPES = [
    ('menu', _('Menu')),
    ('model_view', _('Model View')),
]

MODEL_VIEW_TYPES = [
    ('list', _('List View')),
    ('form', _('Form View')),
]

class RevAction(models.RevModel):

    _description = 'Rev App UI Action'
    
    name = fields.TextField(_('Action Name'))
    type = fields.SelectionField(_('Action Type'), ACTION_TYPES)
    
    # Fields for 'model_view' actions:
    model = fields.TextField(_('Model Name'), required=False)
    view_type = fields.MultiSelectionField(_('View Type List'), MODEL_VIEW_TYPES, required=False)
    views = fields.RecordLinkField(_('Menu'), 'RevView', multi=True, required=False)
    filter = fields.JSONField(_('Record Filter'), required=False)
    
    # Fields for 'menu' actions:
    menu = fields.RecordLinkField(_('Menu'), 'RevMenu', required=False)

    _unique = ['name']