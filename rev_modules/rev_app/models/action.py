
from . import MetadataModel
from rev.db import fields
from rev.i18n import translate as _

ACTION_TYPES = [
    ('view', _('Model View')),
]

MODEL_VIEW_TYPES = [
    ('list', _('List View')),
    ('form', _('Form View')),
]

class Action(MetadataModel):

    _description = 'Rev App UI Action'
    
    id = fields.RecordIDField(_('Action ID'))
    name = fields.TextField(_('Action Name'))
    type = fields.SelectionField(_('Action Type'), ACTION_TYPES)
    
    # Fields for 'model_view' actions:
    model = fields.TextField(_('Model Name'), required=False)
    view_types = fields.MultiSelectionField(_('View Type List'), MODEL_VIEW_TYPES, required=False)
    views = fields.RecordLinkField(_('Linked Views'), 'View', multi=True, required=False)
    filter = fields.JSONField(_('Record Filter'), required=False)
