
import rev
import os

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
    
    for data_file in data_files:
        if data_file[-5:] == '.yaml':
            print(data_file)
