
from rev.db import Model, fields
from rev.i18n import translate as _

from rev.db.exceptions import ValidationError
from rev.http import RevHTTPController

from .loader import load_config_file, load_data, get_module_data_hash

from toposort import toposort_flatten
import importlib
import os, sys
import logging

MODULE_STATUSES = [
    ('not_installed', _('Not Installed')),
    ('to_install', _('To Be Installed')),
    ('installed', _('Installed')),
    ('to_update', _('To Be Updated')),
    ('to_remove', _('To Be Removed')),
]

MODULE_META_CONFIG_KEYS = ['module_name', 'module_description', 'module_version', 'depends']

# Module Metadata container and business logic

class Module(Model):

    _description = 'Rev Module Information'
    
    name = fields.TextField(_('Module Package Name'))
    module_name = fields.TextField(_('Module Name'))
    module_description = fields.TextField(_('Description'), required=False)
    module_version = fields.TextField(_('Module Version'))
    db_version = fields.TextField(_('Installed Version'))
    status = fields.SelectionField(_('Status'), MODULE_STATUSES, default_value='not_installed')
    module_data_hash = fields.TextField(_('Module Data Checksum'), required=False)
    depends = fields.MultiSelectionField(_('Dependancies'), None, required=False)
    
    _unique = ['name']
        
    def get_module_metadata_changes(self, available_modules):
        """
        Takes a dictionary of module information and compares it to the
        module information currently held in the database.
        
        Returns a dictionary with the following keys (if they apply):
        
         - 'new_modules' - list of module names that do not exist in the database
         - 'changed_modules' - dictionary of module name -> list of changes
         - 'removed_modules' - list of modules that do not exist on disk
        """
        res = {}
                
        for mod_name in available_modules:
            db_mod_info = self.find({'name' : mod_name}, read_fields='*')
            
            if not db_mod_info:
                res.setdefault('new_modules', []).append(mod_name)
            
            else:
                # Check for changes to module metadata
                db_mod_info = db_mod_info[0]
                
                def _add_change(module_name, change_type, change_desc):
                    res.setdefault('changed_modules', {}).setdefault(module_name, {}).setdefault(change_type, []).append(change_desc)

                for meta_key in MODULE_META_CONFIG_KEYS:
                    meta_value = available_modules[mod_name].get(meta_key)
                    if meta_value and meta_value != db_mod_info[meta_key]:
                        _add_change(mod_name, 'updated', meta_key)
                
        missing_modules = self.find({'name' : {'$nin' : list(available_modules.keys())}}, read_fields=['name'])
        if missing_modules:
            for mod in missing_modules:
                res.setdefault('removed_modules', []).append(mod['name'])
        
        return res
    
    def get_scheduled_operations(self):
        
        ops = {
            'to_install' : [],
            'to_update' : [],
            'to_remove' : [],
        }
        
        op_modules = self.find({
            'status' : {'$in' : ['to_install', 'to_update', 'to_remove']}
        }, read_fields=['name','status'])
        
        for op in op_modules:
            ops[op['status']].append(op['name'])
        
        return ops

    def get_state_changes_needed(self, installed_modules):
        """
        Using the INSTALLED_MODULES setting, work out which modules should
        be installed or can be removed.
        """

        ops = {
            'install' : [],
            'remove' : [],
        }

        # Find any modules in INSTALLED_MODULES that are not installed

        mods_to_install = self.find({
                'name' : {'$in' : installed_modules},
                'status' : {'$nin' : ['installed', 'to_install', 'to_update']}
            }, read_fields=['name','status'])
        
        for op in mods_to_install:
            ops['install'].append(op['name'])
        
        # Work out the list modules that are no longer needed
        
        mod_depend_info = self.find({
                'status' : {'$in' : ['installed','to_install','to_update']}
            },read_fields=['name','depends'])

        mod_depend_dict = {}
        for mod in mod_depend_info:
            mod_depend_dict[mod['name']] = {
                'depends' : mod['depends'],
                'required' : True if mod['name'] in installed_modules else False
            }
        
        def tag_module_dependancies(mod_info):
            for dep_mod in mod_info['depends']:
                if dep_mod in mod_depend_dict:
                    dep_mod_info = mod_depend_dict[dep_mod]
                    if not dep_mod_info['required']:
                        dep_mod_info['required'] = True
                        tag_module_dependancies(dep_mod_info)

        
        for mod in installed_modules:
            if mod in mod_depend_dict:
                tag_module_dependancies(mod_depend_dict[mod])
                        
        for mod in mod_depend_dict.keys():
            if not mod_depend_dict[mod]['required']:
                ops['remove'].append(mod)
        
        return ops
    
    def _get_module_db_vals(self, module_name, module_info):
        """
        Take values from the module configuration and build the data needed
        for a rev.modules record
        """
        module_meta = {}
        module_meta['name'] = module_name
        for key in MODULE_META_CONFIG_KEYS:
            module_meta[key] = module_info.get(key, None)
             
    def update_module_metadata(self, available_modules):
        """
        Takes a dictionary of module information and updates the
        module information currently held in the database.
        """
        
        module_changes = self.get_module_metadata_changes(available_modules)
        
        if module_changes:
            
            if 'new_modules'in module_changes:
                for mod_name in module_changes['new_modules']:
                    mod_vals = self._get_module_db_vals(mod_name, available_modules[mod_name])
                    mod_vals['db_version'] = mod_vals['module_version'] 
                    mod_id = self.create(mod_vals)
            
            if 'changed_modules' in module_changes:
                for mod_name in module_changes['changed_modules']:
                    mod_vals = self._get_module_db_vals(mod_name, available_modules[mod_name])
                    self.update({'name' : mod_name}, mod_vals)
            
            if 'removed_modules' in module_changes and module_changes['removed_modules']:
                #FIX ME!
                del_ids = [db_ids[mod_name] for mod_name in module_changes['removed_modules']]
                self.delete({'id':{'$in':del_ids}})

    def schedule_operations(self, operations_dict):
        for op in ['remove','update','install']:
            if op in operations_dict.keys():
                self.schedule_operation(op, operations_dict[op])
    
    def schedule_operation(self, operation,  module_names, dependency_stack=[]):
        """
        Schedules the install, update or removal of the specified modules and their dependencies
        
        Operation can be 'install', 'update' or 'remove'
        
        Returns True when done
        """

        for mod in module_names:
            if mod in dependency_stack:
                raise ValidationError("Circular Module Dependency Detected for module '{}': {}".format(
                                                mod, ' -> '.join(dependency_stack)))
        
        mod_data = self.find({'name' : {'$in' : module_names}}, read_fields='*')
        mod_data = dict( [(mod['name'], mod) for mod in mod_data] )
                
        for mod in module_names:
            if mod not in mod_data:
                if dependency_stack:
                    raise ValidationError("Unknown Module '{}' required by '{}'".format(
                                                mod, ' -> '.join(dependency_stack)))
                else:
                    raise ValidationError("Unknown Module '{}'".format(mod))
                        
            if operation == 'install':
                # If this module is not currently installed, install it!
                if mod_data[mod]['status'] == 'not_installed':
                    self.update({'name':mod_data[mod]['name']}, {'status' : 'to_install'})
                elif mod_data[mod]['status'] == 'to_remove':
                    self.update({'name':mod_data[mod]['name']}, {'status' : 'installed'})
                # Make sure all current dependencies are installed as well
                if mod_data[mod]['depends']:
                    dstack = dependency_stack.copy()
                    dstack.append(mod)
                    self.schedule_operation('install', mod_data[mod]['depends'], dstack)
            
            elif operation == 'update':
                # if this module is not installed, then we should install it
                if mod_data[mod]['status'] == 'not_installed':
                    self.update({'name':mod_data[mod]['name']}, {'status' : 'to_install'})
                    # Make sure all current dependencies are installed as well
                    # (only do this if it was not installed)
                    if mod_data[mod]['depends']:
                        self.schedule_operation('install', mod_data[mod]['depends'], [])
                
                elif mod_data[mod]['status'] == 'installed':
                    self.update({'name':mod_data[mod]['name']}, {'status' : 'to_update'})
                    # Make sure all installed modules that depend on this one are also scheduled for an update
                    dep_mods = self.find({'status' : 'installed', 'depends' : mod}, read_fields=['name'])
                    if dep_mods:
                        dstack = dependency_stack.copy()
                        dstack.append(mod)
                        self.schedule_operation('update', [m['name'] for m in dep_mods], dstack)
            
            elif operation == 'remove':
                # If this module is scheduled for install, then just cancel that
                if mod_data[mod]['status'] == 'to_install':
                    self.update({'name':mod_data[mod]['name']}, {'status' : 'not_installed'})
                # otherwise mark it for removal, as appropriate
                elif mod_data[mod]['status'] not in ['not_installed', 'to_remove']:
                    self.update({'name':mod_data[mod]['name']}, {'status' : 'to_remove'})
                    # Also make sure any modules that depend on this one are scheduled for removal too
                    dep_mods = self.find({'depends' : mod}, read_fields=['name'])
                    if dep_mods:
                        dstack = dependency_stack.copy()
                        dstack.append(mod)
                        self.schedule_operation('remove', [m['name'] for m in dep_mods], dstack)
                    
        return True

    def cancel_scheduled_operations(self):
        """
        Cancel all pending install / update / remove operations
        """
        mods = self.find({'status' : {'$in' : ['to_install', 'to_update', 'to_remove']}}, read_fields=['name','status'])
        mod_ids = {
            'to_install' : [],
            'to_update' : [],
            'to_remove' : [],
        }
        for mod in mods:
            mod_ids[mod['status']].append(mod['name'])
        if mod_ids['to_install']:
            self.update({'name':{'$in':mod_ids['to_install']}}, {'status' : 'not_installed'})
        if mod_ids['to_update']:
            self.update({'name':{'$in':mod_ids['to_update']}}, {'status' : 'installed'})
        if mod_ids['to_remove']:
            self.update({'name':{'$in':mod_ids['to_remove']}}, {'status' : 'installed'})
                        
    def get_modules_with_changed_data(self):
        """
        Compare module data on-disk with the database, and return a list of modules
        with data that is not synced with the database
        """
        mods_to_check = self.find({'status' : 'installed'}, read_fields=['name','module_data_hash'])
        
        changed_modules = []
        
        for mod in mods_to_check:
            # Import module so we can determine its directory
            mod_m = importlib.import_module(mod['name'])
            module_path = mod_m.__path__[0]
            # Calculate module data hash
            dir_hash = get_module_data_hash(module_path)
            # Compare hashes
            if dir_hash != mod['module_data_hash']:
                changed_modules.append(mod['name'])
        
        return changed_modules
    
    def load_modules(self, syncdb=False):
        """
        Loads the module hierarchy. If any modules are set to be installed /
        upgraded / removed, do that too if do_operations=True
        """
        
        if syncdb:
            # Do module removals first
            mods_to_remove = self.find({'status' : 'to_remove'}, read_fields='*')
            if mods_to_remove:
                mods_to_sort = {}
                removed_mod_info = {}
                for mod in mods_to_remove:
                    mods_to_sort[mod['name']] = set(mod['depends'])
                    removed_mod_info[mod['name']] = mod
                mod_remove_order = toposort_flatten(mods_to_sort)
                mod_remove_order.reverse()
                for mod in mod_remove_order:
                    if mod in removed_mod_info:
                        print('TODO: Remove data for module: ', mod)
                        self.update({'name':mod}, {
                            'status' : 'not_installed',
                        })

        # load modules
        mods_to_sort = {}
        mod_info = {}
        mod_load_order = []

        mods_to_load = self.find({'status' : {'$in' : ['installed','to_install','to_update']}}, read_fields='*')
        
        for mod_rec in mods_to_load:
            mods_to_sort[mod_rec['name']] = set(mod_rec['depends'])
            mod_info[mod_rec['name']] = mod_rec.to_dict()
        
        if mods_to_sort:
            mod_load_order = toposort_flatten(mods_to_sort)
            self._registry.app.module_load_order = mod_load_order
        
        # 1st Pass: Initialise Models and HTTP Controllers
        logging.info('Initialising Modules...')
        for mod in mod_load_order:
            
            logging.debug(' * Initialising Module: ' + mod)
            
            # Import the module
            mod_m = importlib.import_module(mod)
            module_path = mod_m.__path__[0]
            
            # Load __rev__.conf
            mod_info[mod].update(load_config_file(os.path.join(module_path, '__rev__.conf')))
            
            # Update module metadata in app.module_info
            mod_info[mod]['module_path'] = module_path
            self._registry.app.module_info[mod] = mod_info[mod]
                        
            # Run the before-model-load hook (if applicable)
            if getattr(mod_m, 'before_model_load', False):
                mod_m.before_model_load(self._registry.app, mod_info[mod], syncdb)
            
            # Import the module's models (if present)
            has_models = False
            try:
                m = importlib.import_module(mod+'.models')
                has_models = True
            except ImportError as e:
                logging.debug("Can't import '{}': {}".format(mod+'.models', e))
                pass
            
            if has_models:
                src_files = os.listdir(os.path.join(module_path, 'models'))
                src_files.sort() # make sure theres some kind of determinism for module load order
                
                for src_file in src_files:
                    if src_file == '__init__.py' or src_file[-3:] != '.py':
                        continue
                    m = importlib.import_module(mod+'.models.'+src_file[:-3])
                    
                    for msymbol in dir(m):
                        cls = getattr(m, msymbol)
                        if isinstance(cls, type) and issubclass(cls, Model):

                            # Instantiate model and add to registry
                            # to avoid instantiating 'abstract' classes we check if the
                            # class has a _description attrib. (could be improved)
                            
                            # TODO: Need to work out how inheritance is going to happen!
                            mod_inst = None
                            if issubclass(cls, Model) and hasattr(cls, '_description'):
                                mod_inst = cls(self._registry)
                            self._registry.set(cls.__name__, mod_inst)

            # Initialise the module's http controllers
            has_http = False
            try:
                m = importlib.import_module(mod+'.http_controllers')
                has_http = True
            except ImportError:
                pass
            
            if has_http:
                src_files = os.listdir(os.path.join(module_path, 'http_controllers'))
                src_files.sort()
                
                for src_file in src_files:
                    if src_file == '__init__.py' or src_file[-3:] != '.py':
                        continue
                    m = importlib.import_module(mod+'.http_controllers.'+src_file[:-3])
                    
                    for msymbol in dir(m):
                        cls = getattr(m, msymbol)
                        if isinstance(cls, type) and cls is not RevHTTPController and issubclass(cls, RevHTTPController):
                            
                            logging.debug("Registering HTTP Controller: " + cls.__name__)
                            cls.register(self._registry.app)
        
            # Register template path if the module has a 'templates' folder
            template_path = os.path.join(module_path, 'templates')
            if os.path.isdir(template_path):
                self._registry.app.register_template_path(template_path)

            # Run the after-model-load hook (if applicable)
            if getattr(mod_m, 'after_model_load', False):
                mod_m.after_model_load(self._registry.app, mod_info[mod], syncdb)
        
        # 2nd Pass: Check / Load Module XML Data
        for mod in mod_load_order:
            if syncdb and mod_info[mod]['status'] in ['to_install', 'to_update']:
                # Load data from module data folder
                load_result = load_data(mod_info[mod], self._registry)
                if not load_result:
                    logging.error("Error while loading module data!")
                    break
                # Update database metadata
                dir_hash = get_module_data_hash(mod_info[mod]['module_path'])
                self.update({'name':mod_info[mod]['name']}, {
                    'status' : 'installed',
                    'db_version' : mod_info[mod]['module_version'],
                    'module_data_hash' : dir_hash,
                })
                # Run the after-data-load hook (if applicable)
                mod_m = sys.modules[mod]
                if getattr(mod_m, 'after_data_load', False):
                    mod_m.after_data_load(self._registry.app, mod_info[mod])
        
        # 3rd Pass: Run the after-app-load hook for all modules (if applicable)
        logging.debug("Running 'after_app_load' Actions...")
        for mod in mod_load_order:
            mod_m = sys.modules[mod]
            if getattr(mod_m, 'after_app_load', False):
                mod_m.after_app_load(self._registry.app, mod_info[mod], syncdb)
    
    def delete(self, ids, context={}):
        """
        Check that none of the modules we are trying to delete are currently installed!
        """
        inst_mods = self.find({'id' : {'$in' : ids}, 'status' : {'$ne' : 'not_installed'}})
        if inst_mods:
            raise ValidationError('One or more of the modules you are trying to remove is currently installed!')
        
        return super().delete(ids, context)