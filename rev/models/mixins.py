
from . import fields
from .exceptions import XMLImportError
from rev.i18n import translate as _
import re

class XMLDataMixin:
    """
    Adds the capability to have data automatically imported into the model from
    XML files in each module's 'data' directory
    """

    xml_id = fields.TextField(_('XML ID'))
    xml_module = fields.TextField(_('Module'))
    
    def xml_get_lookup_criteria(self, module, xml_id):
        """
        Create search criteria for finding / updating the specified xml_id
        Model types (e.g. InMemoryModels) can override this if the search
        has be done by a combined 'id' value instead of the seperate field
        lookups
        """
        return {'xml_module' : module, 'xml_id' : xml_id}

    def xml_create_from_element(self, module, elem, context={}):
        create_vals = dict(elem.attrib)
        create_vals['xml_id'] = create_vals['id']
        create_vals['xml_module'] = module
        del create_vals['id']
        self.create(create_vals, context)

    def xml_update_from_element(self, module, elem, context={}):
        update_vals = dict(elem.attrib)
        update_vals['xml_id'] = update_vals['id']
        update_vals['xml_module'] = module
        del update_vals['id']
        self.update(self.xml_get_lookup_criteria(module, update_vals['xml_id']), update_vals, 1, context)

    def xml_import_from_element(self, module, elem, context={}):
        
        if 'id' not in elem.attrib:
            raise XMLImportError("Rev Module Data XML elements must all have an 'id' attribute!")
        if not re.match("^[A-Za-z0-9_]*$", elem.attrib['id']):
            raise XMLImportError("XML element 'id' attribute must only contain letters, numbers and underscores.")
        
        matches = self.find(self.xml_get_lookup_criteria(module, elem.attrib['id']))
        
        if len(matches) > 1:
            raise XMLImportError("Multiple matches for {} with id '{}' from module '{}'!".format(
                                    self.__class__.name, elem.attrib['id'], module))
        
        if not matches:
            self.xml_create_from_element(module, elem, context)
        else:
            self.xml_update_from_element(module, elem, context)
