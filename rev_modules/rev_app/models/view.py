
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

def do_view_modification(target_view_source, modify_elem):
    """
    Performs the requested <modify> operation specified in the modify_elem to the target_view_source
    """
    
    xpath = modify_elem.attrib['xpath']
    action = modify_elem.attrib['action']
    position = -1
    if 'position' in modify_elem.attrib:
        try:
            position = int(modify_elem.attrib['position'])
        except Exception:
            raise XMLImportError("<modify> on line {}: 'position' must be an integer.".format(modify_elem.sourceline))
            return
    
    xmldata = StringIO('<View>' + target_view_source + '</View>')
    tree = etree.parse(xmldata)
    
    matches = []
    try:
        matches = tree.xpath(xpath)
    except Exception as e:
        raise XMLImportError("<modify> on line {}: xpath query failed: {}".format(modify_elem.sourceline, e))
        return
    
    if len(matches) > 1:
        raise XMLImportError("<modify> on line {}: xpath matched more than one element in the target view.".format(modify_elem.sourceline))
        return
    elif len(matches) == 0:
        raise XMLImportError("<modify> on line {}: xpath did not match any elements in the target view.".format(modify_elem.sourceline))
        return

    match_elem = matches[0]
    match_index = matches[0].getparent().index(matches[0])
    match_parent = matches[0].getparent() 
    
    if action == 'remove':
        match_parent.remove(match_elem)
    elif action == 'replace':
        match_parent.remove(match_elem)
        new_index = match_index
        for new_element in modify_elem:
            match_parent.insert(new_index, new_element)
            new_index += 1
    elif action == 'insert_before':
        new_index = match_index
        for new_element in modify_elem:
            match_parent.insert(new_index, new_element)
            new_index += 1
    elif action == 'insert_after':
        new_index = match_index + 1
        for new_element in modify_elem:
            match_parent.insert(new_index, new_element)
            new_index += 1
    elif action == 'insert_inside':
        new_index = position
        if position < 0:
            new_index = len(match_elem)
        for new_element in modify_elem:
            match_elem.insert(new_index, new_element)
            new_index += 1
    
    return ''.join([etree.tostring(child_elem, pretty_print=True).decode('utf8') for child_elem in tree.getroot()])


class View(MetadataModel):

    _description = 'Rev App UI View'
    
    id = fields.RecordIDField(_('View ID'))
    name = fields.TextField(_('View Name'))
    type = fields.SelectionField(_('View Type'), MODEL_VIEW_TYPES, required=False)
    model = fields.TextField(_('Model Name'), required=False)
    source = fields.TextField(_('View Source Code'), required=False)
    
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

    def xml_modify_from_element(self, module, xml_id, elem, context={}):
        """
        Apply changes specified in <modify> tags, to the target view's source,
        as well as the standard field updates.
        """
        modify_vals = dict(elem.attrib)
        del modify_vals['modify']
        
        target_view = self.find({'xml_module' : module, 'xml_id' : xml_id}, read_fields=['source'])[0]
        
        view_source = target_view['source']
        
        for node in elem:
            if node.tag is etree.Comment:
                continue
            if node.tag != 'modify':
                raise XMLImportError("Element on line {}: Unexpected element '{}'.".format(node.sourceline, node.tag))
            if 'xpath' not in node.attrib:
                raise XMLImportError("<modify> on line {}: missing 'xpath' attribute.".format(node.sourceline))
            if 'action' not in node.attrib:
                raise XMLImportError("<modify> on line {}: missing 'action' attribute.".format(node.sourceline))
            if node.attrib['action'] not in MODIFY_ACTIONS:
                raise XMLImportError("<modify> on line {}: invalid action '{}'. Valid actions are: {}".format(node.sourceline, node.attrib['action'], MODIFY_ACTIONS))
                                                                
            view_source = do_view_modification(view_source, node)
        
        modify_vals['source'] = view_source
        
        self.update({'xml_module' : module, 'xml_id' : xml_id}, modify_vals, 1, context)

    def get_rendered_view(self, module, view_id, view_context={}):
        """
        Lookup the specified View, and returned the rendered HTML
        """
        target_view = self.find({'xml_module' : module, 'xml_id' : view_id}, read_fields=['source'])
        
        if not target_view:
            return None
        
        app = self._registry.app
        view_html = target_view[0]['source']
        view_template = app.jinja_env.from_string(view_html)
        app.update_template_context(view_context)
        return view_template.render(view_context)
