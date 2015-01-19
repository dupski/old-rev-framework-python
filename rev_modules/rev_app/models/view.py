
from . import MetadataModel
from rev.db import fields
from rev.db.exceptions import XMLImportError
from rev.i18n import translate as _

from lxml import etree
from io import StringIO

ACTION_TYPES = [
    ('menu', _('Menu')),
    ('model_view', _('Model View')),
]

MODEL_VIEW_TYPES = [
    ('list', _('List View')),
    ('form', _('Form View')),
]

MODIFY_ACTIONS = ['insert_before','insert_after','insert_inside','replace','remove']

def do_view_modifications(target_view_source, modify_elems):
    """
    Performs requested <modify> operations specified in the modify_elem to the target_view_source
    """
    
    #print(' * TARGET VIEW ******************************* ')
    #print(target_view_source)
    #print(' * MODIFY VIEW ******************************* ')
    #print(etree.tostring(modify_elems, pretty_print=True).decode('utf8'))
    
    
    xmldata = StringIO('<View>' + target_view_source + '</View>')
    tree = etree.parse(xmldata)
    
    for elem in modify_elems:

        if elem.tag is etree.Comment:
            continue
        if elem.tag != 'modify':
            raise XMLImportError("Element on line {}: Unexpected element '{}'.".format(elem.sourceline, elem.tag))
        if 'xpath' not in elem.attrib:
            raise XMLImportError("<modify> on line {}: missing 'xpath' attribute.".format(elem.sourceline))
        if 'action' not in elem.attrib:
            raise XMLImportError("<modify> on line {}: missing 'action' attribute.".format(elem.sourceline))
        if elem.attrib['action'] not in MODIFY_ACTIONS:
            raise XMLImportError("<modify> on line {}: invalid action '{}'. Valid actions are: {}".format(elem.sourceline, elem.attrib['action'], MODIFY_ACTIONS))

        xpath = elem.attrib['xpath']
        action = elem.attrib['action']
        position = -1
        if 'position' in elem.attrib:
            try:
                position = int(elem.attrib['position'])
            except Exception:
                raise XMLImportError("<modify> on line {}: 'position' must be an integer.".format(elem.sourceline))
                return
        
        matches = []
        try:
            matches = tree.xpath(xpath)
        except Exception as e:
            raise XMLImportError("<modify> on line {}: xpath query failed: {}".format(elem.sourceline, e))
            return
        
        if len(matches) > 1:
            raise XMLImportError("<modify> on line {}: xpath matched more than one element in the target view.".format(elem.sourceline))
            return
        elif len(matches) == 0:
            raise XMLImportError("<modify> on line {}: xpath did not match any elements in the target view.".format(elem.sourceline))
            return
    
        match_elem = matches[0]
        match_index = matches[0].getparent().index(matches[0])
        match_parent = matches[0].getparent() 
        
        if action == 'remove':
            match_parent.remove(match_elem)
        elif action == 'replace':
            match_parent.remove(match_elem)
            new_index = match_index
            for new_element in elem:
                match_parent.insert(new_index, new_element)
                new_index += 1
        elif action == 'insert_before':
            new_index = match_index
            for new_element in elem:
                match_parent.insert(new_index, new_element)
                new_index += 1
        elif action == 'insert_after':
            new_index = match_index + 1
            for new_element in elem:
                match_parent.insert(new_index, new_element)
                new_index += 1
        elif action == 'insert_inside':
            new_index = position
            if position < 0:
                new_index = len(match_elem)
            for new_element in elem:
                match_elem.insert(new_index, new_element)
                new_index += 1
    
    return ''.join([etree.tostring(child_elem, pretty_print=True).decode('utf8') for child_elem in tree.getroot()])


class View(MetadataModel):

    _description = 'Rev App UI View'
    
    id = fields.RecordIDField(_('View ID'))
    name = fields.TextField(_('View Name'), required=False)
    type = fields.SelectionField(_('View Type'), MODEL_VIEW_TYPES, required=False)
    model = fields.TextField(_('Model Name'), required=False)
    source = fields.TextField(_('View Source Code'))
    modify = fields.TextField(_('Modify View XML ID'), required=False)
    
    def xml_create_from_element(self, module, elem, context={}):
        create_vals = dict(elem.attrib)
        create_vals['xml_id'] = create_vals['id']
        create_vals['xml_module'] = module
        create_vals['source'] = ''.join([etree.tostring(child_elem, pretty_print=True).decode('utf8') for child_elem in elem])
        del create_vals['id']
        self.create(create_vals, context)

    def xml_update_from_element(self, module, elem, context={}):
        update_vals = dict(elem.attrib)
        update_vals['source'] = ''.join([etree.tostring(child_elem, pretty_print=True).decode('utf8') for child_elem in elem])
        del update_vals['id']
        self.update({'xml_module' : module, 'xml_id' : elem.attrib['id']}, update_vals, 1, context)

    def xml_modify_from_element(self, module, elem, target_xml_module, target_xml_id, context={}):
        """
        Apply changes specified in <modify> tags, to the target view's source,
        as well as the standard field updates.
        """
        modify_vals = dict(elem.attrib)
        del modify_vals['id']
        del modify_vals['modify']
        if modify_vals:
            self.update({'xml_module' : target_xml_module, 'xml_id' : target_xml_id}, modify_vals, 1, context)
        
        # As well as updating the target View metadata, we also store the view modifications in a seperate record
        # This allows us update the view data of individual modules, without having to reload all modules that
        # override the view. We avoid having to 'recompile' views at every access via caching.
        
        # Do a test compile of the view first
        self.get_compiled_view(target_xml_module, target_xml_id, elem)
        
        # Save view modification info
        matches = self.find({'xml_module' : module, 'xml_id' : elem.attrib['id']})
        if len(matches) > 1:
            raise XMLImportError("Multiple matches for {} with id '{}' from module '{}'!".format(
                                    self.__class__.name, elem.attrib['id'], module))
        if not matches:
            self.xml_create_from_element(module, elem, context)
        else:
            self.xml_update_from_element(module, elem, context)

        
    def get_compiled_view(self, module, view_id, additional_modify_elems=None):
        """
        Compile view template from its original source, plus any views that modify it
        
        Optionally specify additional modifications via the 'additional_modify_elems'
        parameter, which should be a parent node of a set of <modify> xml element objects
        """

        base_view = self.find({'xml_module' : module, 'xml_id' : view_id}, read_fields=['source'])[0]
        if not base_view:
            return None
        
        view_source = base_view['source']
        
        modify_views = self.find({'modify' : '{}.{}'.format(module, view_id)}, read_fields=['xml_module','xml_id','source'])
        
        if modify_views:
            # Cache and index views by module and xml_id
            views_index = {}
            for mview in modify_views:
                views_index.setdefault(mview['xml_module'], {})[mview['xml_id']] = mview['source']
            
            # Load override views in module load order, then alphabetically by xml_id (so there is determinism)
            for mod in self._registry.app.module_load_order:
                if mod in views_index:
                    view_id_list = list(views_index[mod].keys())
                    view_id_list.sort()
                    
                    for view_id in view_id_list:
                        modify_xml_data = StringIO('<View>' + views_index[mod][view_id] + '</View>')
                        tree = etree.parse(modify_xml_data)
                        modify_elems = tree.getroot()
                        
                        view_source = do_view_modifications(view_source, modify_elems)
        
        if additional_modify_elems is not None and len(additional_modify_elems):
            view_source = do_view_modifications(view_source, additional_modify_elems)
        
        return view_source


    def get_rendered_view(self, module, view_id, view_context={}):
        """
        Lookup the specified View, and returned the rendered HTML
        """
        view_html = self.get_compiled_view(module, view_id)
        
        if not view_html:
            return None
        
        app = self._registry.app
        view_template = app.jinja_env.from_string(view_html)
        app.update_template_context(view_context)
        return view_template.render(view_context)
