
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

def get_xml_child_element_string(parent_node):
    """
    Returns a string concatenation of all child nodes of the specified parent
    """
    return ''.join([etree.tostring(child_elem, pretty_print=True).decode('utf8') for child_elem in parent_node])

def apply_view_modifications(base_view_source, modify_views):
    """
    Apply changes specified in the stack of modify_views to the target view.
    
    base_view_source - base view xml string
    modify_view_sources - list of tuples with details of modify views. Tuples
    should be in the format (module, view_id, view_source)
    """
    
    #from pprint import pprint
    #print('BASE VIEW:\n' + base_view)
    #print('MODIFY VIEWS:')
    #pprint(modify_views)
    
    base_xmldata = StringIO('<View>' + base_view_source + '</View>')
    view_tree = etree.parse(base_xmldata)
    
    for modify_view_source in modify_views:
        
        m_view_module, m_view_id, m_view_source = modify_view_source
        modify_view_id = "{}.{}".format(m_view_module, m_view_id)
        modify_xmldata = StringIO('<View>' + m_view_source + '</View>')
        modify_tree = etree.parse(modify_xmldata)
        
        for elem in modify_tree.getroot():
    
            if elem.tag is etree.Comment:
                continue
            if elem.tag != 'modify':
                raise XMLImportError("Unexpected element '{}'. (View ID: {})".format(elem.tag, modify_view_id))
            if 'xpath' not in elem.attrib:
                raise XMLImportError("<modify> missing 'xpath' attribute. (View ID: {})".format(modify_view_id))
            if 'action' not in elem.attrib:
                raise XMLImportError("<modify> missing 'action' attribute. (View ID: {})".format(modify_view_id))
            if elem.attrib['action'] not in MODIFY_ACTIONS:
                raise XMLImportError("<modify> invalid action '{}'. Valid actions are: {}. (View ID: {})".format(elem.attrib['action'], MODIFY_ACTIONS, modify_view_id))
    
            xpath = elem.attrib['xpath']
            action = elem.attrib['action']
            position = -1
            if 'position' in elem.attrib:
                try:
                    position = int(elem.attrib['position'])
                except Exception:
                    raise XMLImportError("<modify> 'position' attribute value must be an integer. (View ID: {})".format(modify_view_id))
            
            matches = []
            try:
                matches = view_tree.xpath(xpath)
            except Exception as e:
                raise XMLImportError("<modify> xpath query failed: {} (View ID: {})".format(e, modify_view_id))
            
            if len(matches) > 1:
                raise XMLImportError("<modify> xpath matched more than one element in the target view. (View ID: {})\n\n **** TARGET VIEW ****\n\n{}\n\n **** MODIFICATION ****\n\n{}\n"
                                        .format(modify_view_id,
                                                get_xml_child_element_string(view_tree.getroot()).strip(),
                                                etree.tostring(elem, pretty_print=True).decode('utf8').strip()))
            
            elif len(matches) == 0:
                raise XMLImportError("<modify> xpath did not match any elements in the target view. (View ID: {})\n\n **** TARGET VIEW ****\n\n{}\n\n **** MODIFICATION ****\n\n{}\n"
                                        .format(modify_view_id,
                                                get_xml_child_element_string(view_tree.getroot()).strip(),
                                                etree.tostring(elem, pretty_print=True).decode('utf8').strip()))
        
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
    
    return get_xml_child_element_string(view_tree.getroot())

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
        create_vals['source'] = get_xml_child_element_string(elem)
        del create_vals['id']
        self.create(create_vals, context)

    def xml_update_from_element(self, module, elem, context={}):
        update_vals = dict(elem.attrib)
        update_vals['source'] = get_xml_child_element_string(elem)
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
            # Apply view attribute changes to target view
            self.update({'xml_module' : target_xml_module, 'xml_id' : target_xml_id}, modify_vals, 1, context)
        
        # As well as updating the target View metadata, we also store the view modifications in a seperate record
        # This allows us update the view data of individual modules, without having to reload all modules that
        # override the view. We avoid having to 'recompile' views at every access via caching.
        
        # First, do a test compile of the base view with this additional modification included
        test_modify_view = (module, elem.attrib['id'], get_xml_child_element_string(elem))
        self.get_compiled_view(target_xml_module, target_xml_id, test_modify_view)
        
        # Save view modification info
        matches = self.find({'xml_module' : module, 'xml_id' : elem.attrib['id']})
        if len(matches) > 1:
            raise XMLImportError("Multiple matches for {} with id '{}' from module '{}'!".format(
                                    self.__class__.name, elem.attrib['id'], module))
        if not matches:
            self.xml_create_from_element(module, elem, context)
        else:
            self.xml_update_from_element(module, elem, context)

        
    def get_compiled_view(self, base_view_module, base_view_id, test_modify_view=None):
        """
        Compile view template from its original source, plus any views that modify it
        
        Optionally specify 'test_modify_view' parameter, which is a tuple in the format
        (xml_module, xml_id, modify_view_source), and will be injected into the view
        stack at the appropriate place in order to check its compatibility with
        existing views.
        """

        base_view_rec = self.find({'xml_module' : base_view_module, 'xml_id' : base_view_id}, read_fields=['source'])[0]
        if not base_view_rec:
            return None
        
        base_view_source = base_view_rec['source']
        
        modify_view_recs = self.find({'modify' : '{}.{}'.format(base_view_module, base_view_id)}, read_fields=['xml_module','xml_id','source'])
        
        tm_view_module, tm_view_id, tm_view_source = test_modify_view if test_modify_view else (None, None, None)
        
        if not modify_view_recs:
            
            if tm_view_source:
                return apply_view_modifications(base_view_source, [tm_view_source])
            else:
                return base_view_source
        
        else:
            
            # Cache and index views by module and xml_id
            views_index = {}
            for mview in modify_view_recs:
                views_index.setdefault(mview['xml_module'], {})[mview['xml_id']] = mview['source']
            
            if test_modify_view and tm_view_module not in views_index:
                views_index[tm_view_module] = {}
            
            modify_views = []
            
            # Load modify views in module load order, then alphabetically by xml_id (so there is determinism)
            for mod in self._registry.app.module_load_order:
                if mod in views_index:
                    view_id_list = list(views_index[mod].keys())
                    if test_modify_view and mod == tm_view_module and tm_view_id not in view_id_list:
                        view_id_list.append(tm_view_id)
                    view_id_list.sort()
                    for view_id in view_id_list:
                        if test_modify_view and mod == tm_view_module and view_id == tm_view_id:
                            # test out the modifications
                            modify_views.append((tm_view_module, tm_view_id, tm_view_source))
                            return apply_view_modifications(base_view_source, modify_views)
                        else:
                            modify_views.append((mod, view_id, views_index[mod][view_id]))
        
            return apply_view_modifications(base_view_source, modify_views)

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
