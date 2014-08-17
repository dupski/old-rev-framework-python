
from rev.core.models import RevModel
from rev.core import fields
from rev.core.translations import translate as _

MODULE_STATUSES = [
    ('not_installed', _('Not Installed')),
    ('to_install', _('To Be Installed')),
    ('installed', _('Installed')),
]

class RevModules(RevModel):

    _name = 'rev.modules'
    _description = 'Rev Module Information'
    
    name = fields.TextField(_('Module Name'))
    description = fields.TextField(_('Description'))
    version = fields.TextField(_('Version'))
    status = fields.SelectionField(_('Status'))