
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
        
    def __init__(self, *args, **kwargs):
        # Cache xml_ids for this model to detect duplicate when importing
        self._imported_xml_ids = []
        # Add unique constraint for xml_module and xml_id
        if hasattr(self, '_unique'):
            self._unique.append( ('xml_module', 'xml_id') )
        else:
            self._unique = [ ('xml_module', 'xml_id') ]
        # Make sure any Model or Mixin classes are __init__'ed
        super().__init__(*args, **kwargs)

    def xml_create_from_element(self, module, elem, context={}):
        create_vals = dict(elem.attrib)
        create_vals['xml_id'] = create_vals['id']
        create_vals['xml_module'] = module
        del create_vals['id']
        self.create(create_vals, context)

    def xml_update_from_element(self, module, elem, context={}):
        update_vals = dict(elem.attrib)
        del update_vals['id']
        self.update({'xml_module' : module, 'xml_id' : elem.attrib['id']}, update_vals, 1, context)

    def xml_modify_from_element(self, module, xml_id, elem, context={}):
        modify_vals = dict(elem.attrib)
        del modify_vals['modify']
        if modify_vals:
            self.update({'xml_module' : module, 'xml_id' : xml_id}, modify_vals, 1, context)
    
    def xml_import_from_element(self, module, elem, context={}):

        if 'id' not in elem.attrib and 'modify' not in elem.attrib \
          or ('id' in elem.attrib and 'modify' in elem.attrib):
            raise XMLImportError("XML elements must have either an 'id' or a 'modify' attribute.")
        
        if 'id' in elem.attrib:
            if not re.match("^[A-Za-z0-9_]*$", elem.attrib['id']):
                raise XMLImportError("'id' attribute must only contain letters, numbers and underscores.")
        
            xml_id_str = "{}.{}".format(module, elem.attrib['id'])
            if xml_id_str in self._imported_xml_ids:
                raise XMLImportError("Duplicated XML element id '{}' in module '{}'.".format(elem.attrib['id'], module))
            else:
                self._imported_xml_ids.append(xml_id_str)

            matches = self.find({'xml_module' : module, 'xml_id' : elem.attrib['id']})
        
            if len(matches) > 1:
                raise XMLImportError("Multiple matches for {} with id '{}' from module '{}'!".format(
                                        self.__class__.name, elem.attrib['id'], module))
            
            if not matches:
                self.xml_create_from_element(module, elem, context)
            else:
                self.xml_update_from_element(module, elem, context)

        elif 'modify' in elem.attrib:
        
            view_id = elem.attrib['modify'].split('.')
            
            if len(view_id) != 2:
                raise XMLImportError("'modify' attribute must be in the format '<module_name>.<xml_id>'.")
            
            matches = self.find({'xml_module' : view_id[0], 'xml_id' : view_id[1]})
            
            if not matches:
                raise XMLImportError("Could not find {} '{}' specified in the 'modify' attribute. You might need to check your module's dependencies.".format(elem.tag, elem.attrib['modify']))
            
            self.xml_modify_from_element(view_id[0], view_id[1], elem, context)

