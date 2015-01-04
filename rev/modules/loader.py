
from . import Module
from rev.models import InMemoryModel
from rev.models.mixins import XMLDataMixin
from rev.models.exceptions import XMLImportError, ValidationError

import logging
import os, sys
import imp
from lxml import etree

def get_available_modules(app):
    """
    Scan the app's MODULE_PATHS and return a dictionary of all the available module metadata
    
    raises exceptions when module definitions are invalid
    """
    
    available_modules = {}
    
    # Check specified module paths and collect metadata
    logging.info("Module Paths: " + ','.join(app.settings['MODULE_PATHS']))

    mod_path_list = app.settings['MODULE_PATHS']
    for mod_path in mod_path_list:
        if not os.path.isdir(mod_path):
            raise Exception("Module Path '{}' is not a directory!".format(mod_path))
        
        mod_folders = [name for name in os.listdir(mod_path)
                        if os.path.isdir(os.path.join(mod_path, name))]
        for mod_folder in mod_folders:
            try:
                mod_info = imp.find_module(mod_folder)
                logging.warning("Module '{}' masks existing module at '{}'".format(mod_folder, mod_info[1]))
            except:
                pass

            rev_conf_file = os.path.join(mod_path, mod_folder, '__rev__.conf')
            
            if not os.path.isfile(rev_conf_file):
                raise Exception("Module '{}' has no __rev__.conf file".format(mod_folder))
            
            module_info = {}
            exec(open(rev_conf_file).read(), {}, module_info)            

            if module_info.get('depends') == None:
                raise Exception("Module '{}' __rev__.conf does not contain any dependency information".format(mod_folder))
            
            available_modules[mod_folder] = module_info
    
    return available_modules

def get_module_meta_change_description(meta_changes):
    meta_change_str = 'The following module metadata differences were detected between this installation and the database:'
    if 'new_modules' in meta_changes:
        meta_change_str += '\nNEW MODULES: ' + ', '.join(meta_changes['new_modules'])
    if 'removed_modules' in meta_changes:
        meta_change_str += '\nREMOVED MODULES: ' + ', '.join(meta_changes['removed_modules'])
    if 'changed_modules' in meta_changes:
        meta_change_str += '\nCHANGED MODULES: '
        for mod_name, mod_change in meta_changes['changed_modules'].items():
            meta_change_str += '\n  MODULE: ' + mod_name
            if 'updated' in mod_change:
                meta_change_str += '\n    UPDATED KEYS: ' + ', '.join(mod_change['updated'])
    return meta_change_str

def get_scheduled_operation_description(ops):
    op_str = 'The following module operations are pending:'
    if ops['to_install']:
        op_str += '\nThe following modules are due to be INSTALLED:'
        op_str += '\n  ' + ', '.join(ops['to_install'])
    if ops['to_update']:
        op_str += '\nThe following modules are due to be UPDATED:'
        op_str += '\n  ' + ', '.join(ops['to_update'])
    if ops['to_remove']:
        op_str += '\nThe following modules are due to be REMOVED:'
        op_str += '\n  ' + ', '.join(ops['to_remove'])
    return op_str

def get_required_changes_description(ops):
    op_str = ''
    if ops['install']:
        op_str += '\nBased on your INSTALLED_MODULES setting, the following modules need to be INSTALLED:'
        op_str += '\n  ' + ', '.join(ops['install'])
    if ops['remove']:
        op_str += '\nBased on your INSTALLED_MODULES setting, the following modules need to be REMOVED:'
        op_str += '\n  ' + ', '.join(ops['remove'])
    return op_str


def load_data(mod_info, registry, syncdb):

    """
    Loads all data from .yaml files in a module's data directory
    """
    data_path = os.path.join(mod_info['module_path'], 'data')
    
    if not os.path.isdir(data_path):
        return False

    logging.info('Loading Module Data for '+mod_info['name'])

    for root, dirs, files in os.walk(data_path):
        for filename in files:
            if filename[-4:] != '.xml':
                continue

            xml_path = os.path.join(root, filename)
            logging.debug("Loading '{}'".format(xml_path))

            xmltree = None
            try:
                xmltree = etree.parse(xml_path)
            except Exception as e:
                logging.error("Error loading {}: {}".format(xml_path, e))
                continue
            
            xml_root = xmltree.getroot()
            
            for elem in xml_root:
                if elem.tag is etree.Comment:
                    continue
                if not registry.model_exists(elem.tag):
                    logging.error("Error on line {} of {}: Model '{}' does not exist.".format(elem.sourceline, xml_path, elem.tag))
                    continue
                mod = registry.get(elem.tag)
                if not isinstance(mod, XMLDataMixin):
                    logging.error("Error on line {} of {}: Model '{}' does not support XML Import.".format(elem.sourceline, xml_path, elem.tag))
                    continue
                
                # Load item only if syncdb is enabled, or if the model is an InMemoryModel
                if isinstance(mod, InMemoryModel) or syncdb:
                    try:
                        mod.xml_import_from_element(mod_info['name'], elem)
                    except (XMLImportError, ValidationError) as e:
                        logging.error("Error on line {} of {}: {} XML Import Error: {}".format(elem.sourceline, xml_path, elem.tag, e))
                        continue
    
    return True