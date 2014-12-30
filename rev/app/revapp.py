
from flask import Flask
from jinja2 import FileSystemLoader, ChoiceLoader

import logging
import importlib
import sys

from rev.db.models import RevModelRegistry
from rev.modules.module import RevModule

# Main RevFramework Application object

class RevApp(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        block_start_string='@{%',
        block_end_string='%}',
        variable_start_string='@{{',
        variable_end_string='}}',
        comment_start_string='@{#',
        comment_end_string='#}',
    ))
    
    def __init__(self, app_name, settings, *args, **kwargs):

        # Initialise instance variables
        self.registry = None
        self.template_paths = []
        self.module_info = {}
                
        # Load settings module into self.settings
        self.name = app_name
        self.settings = {}
        for setting in dir(settings):
            if setting.isupper():
                self.settings[setting] = getattr(settings, setting)
        
        # Hardcode the flask import_name to 'rev'. Template and static file paths are sorted out later.
        return super().__init__('rev', *args, **kwargs)

    def register_template_path(self, template_path):
        self.template_paths.append(template_path)
    
    def init(self, syncdb=False):
        """
        Initialiseconfiguration, database and installed modules
        """
        
        # intialise default database
        default_db_config = self.settings['DATABASES']['default']
        db_prov_module = importlib.import_module(default_db_config['provider'])
        db_prov_class = getattr(db_prov_module, 'DatabaseProvider')
        
        db_prov = db_prov_class(default_db_config)
        
        # initialise model registry
        self.registry = RevModelRegistry(self, db_prov)
        
        from rev.modules import loader
        
        # load modules
        available_modules = loader.get_available_modules(self)
        
        # Module paths validated. Add them to python path
        for mod_path in self.settings['MODULE_PATHS']:
            if mod_path not in sys.path:
                sys.path.insert(0, mod_path)
                    
        # Initialise the RevModule model
        module_obj = RevModule(self.registry)
    
        # Check for installed module metadata differences
        logging.info("Checking Module Metadata...")
        meta_changes = module_obj.get_module_metadata_changes(available_modules)
                
        # Log a warning if this is the case, or perform update if syncdb-True
        if meta_changes:
            meta_change_str = loader.get_module_meta_change_description(meta_changes)
            if not syncdb:
                meta_change_str += "\nYou should run './app.py syncdb' to update the database."
                logging.warning(meta_change_str)
            else:
                logging.info(meta_change_str)
                module_obj.update_module_metadata(available_modules)
                logging.info('Module Metadata Successfully Updated.')
        elif syncdb:
            logging.info('Database Module Metadata is up to date.')

        # Check that the status of modules in INSTALLED_MODULES matches the database
        req_state_changes = module_obj.get_state_changes_needed(
                                            self.settings['INSTALLED_MODULES'])
        
        # Log a warning if this is the case, or schedule operations if syncdb=True
        if req_state_changes['install'] or req_state_changes['remove']:
            op_str = loader.get_required_changes_description(req_state_changes)
            if not syncdb:
                op_str += "\nYou should run './app.py syncdb' to apply these changes."
                logging.warning(op_str)
            else:
                module_obj.schedule_operations(req_state_changes)
        elif syncdb:
            logging.info('No changes detected to INSTALLED_MODULES setting.')
        
        # If syncdb=True, schedule all installed modules to be updated
        if syncdb:
            installed_modules = module_obj.find({'status' : 'installed'}, read_fields=['name'])
            for mod in installed_modules:
                module_obj.schedule_operation('update', [mod['name']])
            
        # Check if there are pending module operations
        sched_ops = module_obj.get_scheduled_operations()
        
        # Log a warning if this is the case, or prompt the user to apply the changes if syncdb=True
        if sched_ops['to_install'] or sched_ops['to_update'] or sched_ops['to_remove']:
            op_str = loader.get_scheduled_operation_description(sched_ops)
            if not syncdb:
                op_str += "\nYou should run './app.py syncdb' to apply these changes."
                logging.warning(op_str)
            else:
                logging.info(op_str)
                response = ''
                while response not in ['y','n']:
                    response = input("Apply these changes for database '{}'? (y/n): ".format(db_prov.db_name)).lower()
                if response == 'n':
                    response = ''
                    while response not in ['y','n']:
                        response = input("Cancel scheduled install/update/remove operations? (y/n): ").lower()
                    if response == 'y':
                        module_obj.cancel_scheduled_operations()
                        logging.info("Operations Cancelled.")
                    sys.exit(1)

        module_obj.load_modules(do_operations=syncdb)
        
        if not syncdb:
            
            # configure jinja template paths
            template_loaders = [self.jinja_loader]
            for template_path in self.template_paths:
                template_loaders.append(FileSystemLoader(template_path))
            template_loaders.reverse() # Last imported module should take precedence
            self.jinja_loader = ChoiceLoader(template_loaders)
            
            # log endpoints
            logging.debug('Registered HTTP Endpoints:')
            for rule in self.url_map.iter_rules():
                logging.debug('  '+rule.rule+' => '+rule.endpoint)
        