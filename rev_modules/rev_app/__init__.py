
import logging
import os
from lxml import etree
import re

def after_app_load(app, prev_mod_info):
    logging.info("Loading Views for Running Modules...")
    
    for mod in app.module_load_order:
        logging.debug("Module: {}".format(mod))        
        view_dir_path = os.path.join(app.module_info[mod]['module_path'], 'views')
        if os.path.exists(view_dir_path):
            for root, dirs, files in os.walk(view_dir_path):
                for filename in files:
                    if filename[-4:] != '.xml':
                        continue
                    
                    logging.debug("Loading '{}'".format(filename))
                    xml_path = os.path.join(root, filename)
                    xmltree = etree.parse(xml_path)
                    root = xmltree.getroot()
                    
                    for elem in root:
                        if elem.tag != 'rev-view':
                            logging.error("Error on line {} of {}: Unexpected element '{}'.".format(elem.sourceline, xml_path, elem.tag))
                            continue
                        if ('id' not in elem.attrib and 'modify' not in elem.attrib) \
                          or ('id' in elem.attrib and 'modify' in elem.attrib):
                            logging.error("Error on line {} of {}: <rev-view> must have either an 'id' or a 'modify' attribute.".format(elem.sourceline, xml_path))
                            continue
                        if 'id' in elem.attrib and not re.match("^[A-Za-z0-9_]*$", elem.attrib['id']):
                            logging.error("Error on line {} of {}: <rev-view> 'id' attribute must only contain letters, numbers and underscores.".format(elem.sourceline, xml_path))
                            continue
                        
                        print(elem.tag, elem.attrib)
                        print( etree.tostring(elem, pretty_print=True).decode('utf8') )