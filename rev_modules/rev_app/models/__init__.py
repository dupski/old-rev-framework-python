
from rev.models import InMemoryModel, fields
from rev.models.mixins import XMLDataMixin
from rev.i18n import translate as _

class MetadataModel(InMemoryModel, XMLDataMixin):
    """
    Base class for rev_app metadata models
    """
    
    def xml_get_lookup_criteria(self, module, xml_id):
        """
        Create search criteria for finding / updating the specified xml_id
        Model types (e.g. InMemoryModels) can override this if the search
        has be done by a combined 'id' value instead of the seperate field
        lookups
        """
        return {'id' : "{}.{}".format(module, xml_id)}

    def create_record_id(self, vals, context={}):
        """
        InMemory Metadata Record IDs should be '<module>.<xml_id>'
        """
        return "{}.{}".format(vals['xml_module'], vals['xml_id'])

