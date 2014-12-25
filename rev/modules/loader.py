
from .module import RevModule

import logging
import os, sys
import imp
import yaml

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


def load_data(mod_info, mod_path, registry):

    """
    Loads all data from .yaml files in a module's data directory
    """
    data_path = os.path.join(mod_path, 'data')
    
    if not os.path.isdir(data_path):
        return None

    logging.info('Loading Module Data for '+mod_info['name'])

    data_files = os.listdir(data_path)
    data_files.sort()

    from pprint import pformat
    
    for data_file in data_files:
        if data_file[-5:] == '.yaml':
            
            fpath = os.path.join(data_path, data_file)
            logging.info('Loading {}...'.format(data_file))
            
            yaml_data = None
            with open(fpath, 'r') as yaml_file:
                try:
                    yaml_data = yaml.load(yaml_file)
                except yaml.YAMLError as e:
                    logging.error('Error loading YAML file:\n{}'.format(e))
                    sys.exit(1)
                    
            if yaml_data:
                if not isinstance(yaml_data, list):
                    logging.error('Root element of YAML file must be a list')
                    sys.exit(1)

                rec_no = 1
                for rec in yaml_data:
                    if not isinstance(rec, dict):
                        logging.error('YAML record {} is not a dictionary'.format(rec_no))
                        sys.exit(1)
                    
                    if len(rec) == 1 and registry.model_exists(list(rec)[0]):
                        model_name = list(rec)[0]
                        logging.debug('Loading YAML record {} which is a {}\n{}'.format(rec_no, model_name, pformat(rec)))
                    
                    else:
                        logging.error('Could not interpret YAML record {}. Perhaps the model name is incorrect?\n{}'.format(rec_no, pformat(rec)))
                        sys.exit(1)
                    
                    rec_no += 1