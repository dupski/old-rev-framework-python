
import rev
import os
import sys
import yaml

def load_data(mod_info, mod_path, registry):
    """
    Loads all data from .yaml files in a module's data directory
    """
    data_path = os.path.join(mod_path, 'data')
    
    if not os.path.isdir(data_path):
        return
    
    rev.log.info('Loading Module Data for '+mod_info['name'])

    data_files = os.listdir(data_path)
    data_files.sort()

    from pprint import pformat
    
    for data_file in data_files:
        if data_file[-5:] == '.yaml':
            
            fpath = os.path.join(data_path, data_file)
            rev.log.info('Loading {}...'.format(data_file))
            
            yaml_data = None
            with open(fpath, 'r') as yaml_file:
                try:
                    yaml_data = yaml.load(yaml_file)
                except yaml.YAMLError as e:
                    rev.log.error('Error loading YAML file:\n{}'.format(e))
                    sys.exit(1)
                    
            if yaml_data:
                if not isinstance(yaml_data, list):
                    rev.log.error('Root element of YAML file must be a list')
                    sys.exit(1)

                rec_no = 1
                for rec in yaml_data:
                    if not isinstance(rec, dict):
                        rev.log.error('YAML record {} is not a dictionary'.format(rec_no))
                        sys.exit(1)
                    
                    if len(rec) == 1 and registry.model_exists(list(rec)[0]):
                        model_name = list(rec)[0]
                        rev.log.debug('Loading YAML record {} which is a {}\n{}'.format(rec_no, model_name, pformat(rec)))
                    
                    else:
                        rev.log.error('Could not interpret YAML record {}. Perhaps the model name is incorrect?\n{}'.format(rec_no, pformat(rec)))
                        sys.exit(1)
                    
                    rec_no += 1