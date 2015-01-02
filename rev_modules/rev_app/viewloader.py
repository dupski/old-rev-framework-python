
import logging
import os
from lxml import etree
import re
from io import StringIO

MODIFY_ACTIONS = ['insert_before','insert_after','insert_inside','replace','remove']

def do_view_modification(target_view, modify_xml, modify_xml_path):
    
    xpath = modify_xml.attrib['xpath']
    action = modify_xml.attrib['action']
    position = -1
    if 'position' in modify_xml.attrib:
        try:
            position = int(modify_xml.attrib['position'])
        except Exception:
            logging.error("Error in {}, line {}: <modify> 'position' must be an integer.".format(modify_xml_path, modify_xml.sourceline))
            return
    
    xmldata = StringIO(target_view['view'])
    tree = etree.parse(xmldata)
    
    matches = []
    try:
        matches = tree.xpath(xpath)
    except Exception as e:
        logging.error("Error in {}, line {}: <modify> xpath query failed: {}".format(modify_xml_path, modify_xml.sourceline, e))
        return
    
    if len(matches) > 1:
        logging.error("Error in {}, line {}: <modify> xpath matched more than one element in the target view.".format(modify_xml_path, modify_xml.sourceline))
        return
    elif len(matches) == 0:
        logging.error("Error in {}, line {}: <modify> xpath did not match any elements in the target view.".format(modify_xml_path, modify_xml.sourceline))
        return

    match_elem = matches[0]
    match_index = matches[0].getparent().index(matches[0])
    match_parent = matches[0].getparent() 
    
    if action == 'remove':
        match_parent.remove(match_elem)
    elif action == 'replace':
        match_parent.remove(match_elem)
        new_index = match_index
        for new_element in modify_xml:
            match_parent.insert(new_index, new_element)
            new_index += 1
    elif action == 'insert_before':
        new_index = match_index
        for new_element in modify_xml:
            match_parent.insert(new_index, new_element)
            new_index += 1
    elif action == 'insert_after':
        new_index = match_index + 1
        for new_element in modify_xml:
            match_parent.insert(new_index, new_element)
            new_index += 1
    elif action == 'insert_inside':
        new_index = position
        if position < 0:
            new_index = len(match_elem)
        for new_element in modify_xml:
            match_elem.insert(new_index, new_element)
            new_index += 1
    
    target_view['view'] = etree.tostring(tree, pretty_print=True).decode('utf8')
    

def load_views(app):
    """
    Scans and loads views from the 'views' folder of all installed modules.
    Returns a dictionary: [module][view_id] -> {meta:{}, view:''}
    """
    views = {}
    
    for mod in app.module_load_order:
        logging.debug("Module: {}".format(mod))      
        views[mod] = {}  
        view_dir_path = os.path.join(app.module_info[mod]['module_path'], 'views')
        if os.path.exists(view_dir_path):
            for root, dirs, files in os.walk(view_dir_path):
                for filename in files:
                    if filename[-4:] != '.xml':
                        continue
                    
                    logging.debug("Loading '{}'".format(filename))
                    xml_path = os.path.join(root, filename)
                    
                    xmltree = None
                    try:
                        xmltree = etree.parse(xml_path)
                    except Exception as e:
                        logging.error("Error loading {}: {}".format(xml_path, e))
                        continue
                    
                    root = xmltree.getroot()
                    
                    for elem in root:
                        if elem.tag != 'rev-view':
                            logging.error("Error on line {} of {}: Unexpected element '{}'.".format(elem.sourceline, xml_path, elem.tag))
                            continue
                        if ('id' not in elem.attrib and 'modify' not in elem.attrib) \
                          or ('id' in elem.attrib and 'modify' in elem.attrib):
                            logging.error("Error on line {} of {}: <rev-view> must have either an 'id' or a 'modify' attribute.".format(elem.sourceline, xml_path))
                            continue
                        
                        if 'id' in elem.attrib:
                            if not re.match("^[A-Za-z0-9_]*$", elem.attrib['id']):
                                logging.error("Error on line {} of {}: <rev-view> 'id' attribute must only contain letters, numbers and underscores.".format(elem.sourceline, xml_path))
                                continue
                            if elem.attrib['id'] in views[mod]:
                                logging.error("Error on line {} of {}: <rev-view> duplicate 'id' detected: {}".format(elem.sourceline, xml_path, elem.attrib['id']))
                                continue
                            
                            view_meta = dict(elem.attrib)
                            
                            # Remove all attributes from the <rev-view> tag as these will be stored in the 'meta' dict
                            for attrib in elem.attrib.keys():
                                elem.attrib.pop(attrib)
                            
                            views[mod][view_meta['id']] = {
                                'meta' : view_meta,
                                'view' : etree.tostring(elem, pretty_print=True).decode('utf8'),
                            }
                        
                        elif 'modify' in elem.attrib:
                            
                            view_id = elem.attrib['modify'].split('.')
                            
                            if len(view_id) != 2:
                                logging.error("Error on line {} of {}: <rev-view> 'modify' attribute must be in the format '<module_name>.<view_id>'.".format(elem.sourceline, xml_path))
                                continue
                            
                            if view_id[0] not in views or view_id[1] not in views[view_id[0]]:
                                logging.error("Error on line {} of {}: <rev-view> could not find view '{}' specified in the 'modify' attribute. You might need to check your module's dependencies.".format(elem.sourceline, xml_path, elem.attrib['modify']))
                                continue
                            
                            target_view = views[view_id[0]][view_id[1]]
                            
                            for node in elem:
                                if node.tag != 'modify':
                                    logging.error("Error on line {} of {}: Unexpected element '{}'.".format(elem.sourceline, xml_path, elem.tag))
                                    continue
                                if 'xpath' not in node.attrib:
                                    logging.error("Error on line {} of {}: <modify> missing 'xpath' attribute.".format(elem.sourceline, xml_path))
                                    continue
                                if 'action' not in node.attrib:
                                    logging.error("Error on line {} of {}: <modify> missing 'action' attribute.".format(elem.sourceline, xml_path))
                                    continue
                                if node.attrib['action'] not in MODIFY_ACTIONS:
                                    logging.error("Error on line {} of {}: <modify> invalid action '{}'. Valid actions are: {}".format(elem.sourceline, xml_path, node.attrib['action'], MODIFY_ACTIONS))
                                    continue
                                                                
                                do_view_modification(target_view, node, xml_path)

                            meta_update = dict(elem.attrib)
                            del(meta_update['modify'])
                            target_view['meta'].update(meta_update)                                
    
    return views