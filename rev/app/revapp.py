
from flask import Flask
from werkzeug.contrib.cache import SimpleCache
from jinja2 import FileSystemLoader, ChoiceLoader

import logging
import importlib
import sys

from rev import PKG_NAME, PKG_VERSION
from rev.db.registry import ModelRegistry
from rev.modules import Module
from rev.modules.staticfiles import StaticFiles, StaticFilesEndpoint

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
        self.staticfiles = None
        self.template_paths = []
        self.module_info = {}
        self.module_load_order = []
                        
        # Hardcode the flask import_name to 'rev'. Template and static file paths are sorted out later.
        super().__init__('rev', *args, static_folder=None, **kwargs)
        
        # Load settings module into flask app.config
        self.name = app_name
        for setting in dir(settings):
            if setting.isupper():
                self.config[setting] = getattr(settings, setting)
        
        # Configure cache
        # TODO: Support other cache types!
        self.cache = SimpleCache()


    def register_template_path(self, template_path):
        self.template_paths.append(template_path)
    
    def init(self, syncdb=False):
        """
        Initialise configuration, database and installed modules
        
        syncdb can be 'interactive', 'auto' or False
        """

        logging.info('{} v{}'.format(PKG_NAME, PKG_VERSION))
        
        if not syncdb or syncdb == 'auto':
            logging.info("Starting Rev App '{}' ...".format(self.name))
        
        # initialise database providers
        self.databases = {}
        for db_name in self.config['DATABASES'].keys():
            provider_conf = self.config['DATABASES'][db_name]
            prov_module = importlib.import_module(provider_conf['provider'])
            prov_class = getattr(prov_module, 'DatabaseProvider')
            self.databases[db_name] = prov_class(provider_conf, db_name)
        
        # initialise model registry
        self.registry = ModelRegistry(self)
        
        from rev.modules import loader
        
        # load modules
        available_modules = []
        try:
            available_modules = loader.get_available_modules(self)
        except Exception as e:
            logging.error("Error loading modules: {}".format(e))
            sys.exit(2)
        
        # Module paths validated. Add them to python path
        for mod_path in self.config['MODULE_PATHS']:
            if mod_path not in sys.path:
                sys.path.insert(0, mod_path)
                    
        # Initialise the Module model and add it to the registry
        module_obj = Module(self.registry)
        self.registry.set(module_obj.__class__.__name__, module_obj)
    
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
                                            self.config['INSTALLED_MODULES'])
        
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
        
        if syncdb and syncdb == 'interactive':
            # If syncdb='interactive', schedule all installed modules to be updated
            installed_modules = module_obj.find({'status' : 'installed'}, read_fields=['name'])
            for mod in installed_modules:
                module_obj.schedule_operation('update', [mod['name']])
        else:
            # Otherwise, check whether module data matches the database
            changed_modules = module_obj.get_modules_with_changed_data()
            if changed_modules:
                change_str = loader.get_changed_data_description(changed_modules)
                if not syncdb:
                    change_str += "\nYou should run './app.py syncdb' to reload module data."
                    logging.warning(change_str)
                else:
                    logging.info(change_str)
                    module_obj.schedule_operation('update', changed_modules)
        
        # Check if there are pending module operations
        sched_ops = module_obj.get_scheduled_operations()
        
        # Log a warning if this is the case, or prompt the user to apply the changes if syncdb=True
        if sched_ops['to_install'] or sched_ops['to_update'] or sched_ops['to_remove']:
            op_str = loader.get_scheduled_operation_description(sched_ops)
            if not syncdb:
                op_str += "\nYou should run './app.py syncdb' to apply these changes."
                logging.warning(op_str)
            elif syncdb != 'auto':
                logging.info(op_str)
                response = ''
                while response not in ['y','n']:
                    response = input("Apply these changes? (y/n): ").lower()
                if response == 'n':
                    response = ''
                    while response not in ['y','n']:
                        response = input("Cancel scheduled install/update/remove operations? (y/n): ").lower()
                    if response == 'y':
                        module_obj.cancel_scheduled_operations()
                        logging.info("Operations Cancelled.")
                    sys.exit(1)

        module_obj.load_modules(syncdb)
        
        if not syncdb or syncdb == 'auto':
                        
            # initialise static files class
            self.staticfiles = StaticFiles(self)
            StaticFilesEndpoint.register(self)
            
            # configure jinja template paths
            template_loaders = [self.jinja_loader]
            for template_path in self.template_paths:
                template_loaders.append(FileSystemLoader(template_path))
            template_loaders.reverse() # Last imported module should take precedence
            self.jinja_loader = ChoiceLoader(template_loaders)
            
            # set up jinja2 global context
            @self.context_processor
            def jinja_global_context():
                return {'app' : self}
            
            # log endpoints
            logging.debug('Registered HTTP Endpoints:')
            for rule in self.url_map.iter_rules():
                logging.debug('  '+rule.rule+' => '+rule.endpoint)

            logging.info("Rev App '{}' Initialised.".format(self.name))
