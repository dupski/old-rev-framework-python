
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

class RevView(models.RevModel):

    _description = 'Rev App UI Action'
    
    name = fields.TextField(_('View Name'))
    type = fields.SelectionField(_('View Type'), MODEL_VIEW_TYPES)
    model = fields.TextField(_('Model Name'), required=True)
    