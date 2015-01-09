
from rev.db import Model, fields
from rev.db.mixins import XMLDataMixin
from rev.i18n import translate as _

class MetadataModel(Model, XMLDataMixin):
    """
    Base class for rev_app metadata models
    """
