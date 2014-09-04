
import rev
from rev.core.models import RevModel
from rev.core import fields
from rev.core.translations import translate as _

from rev.core.exceptions import ValidationError

from toposort import toposort_flatten
import importlib
import os

MODULE_STATUSES = [
    ('not_installed', _('Not Installed')),
    ('to_install', _('To Be Installed')),
    ('installed', _('Installed')),
    ('to_update', _('To Be Updated')),
    ('to_remove', _('To Be Removed')),
]

class RevModule(RevModel):

    _description = 'Rev Module Information'
    
    name = fields.TextField(_('Module Package Name'))
    module_name = fields.TextField(_('Module Name'))
    module_description = fields.TextField(_('Description'), required=False)
    module_version = fields.TextField(_('Module Version'))
    db_version = fields.TextField(_('Installed Version'))
    status = fields.SelectionField(_('Status'), default_value='not_installed')
    depends = fields.MultiSelectionField(_('Dependancies'), required=False)
    auto_install = fields.BooleanField(_('Automatically Installed?'), required=False)
    
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

                for meta_key, meta_value in available_modules[mod_name].items():
                    
                    # Map conf key names to db names
                    if meta_key == 'name':
                        meta_key = 'module_name'
                    if meta_key == 'description':
                        meta_key = 'module_description'
                    if meta_key == 'version':
                        meta_key = 'module_version'
                    
                    if meta_value != db_mod_info[meta_key]:
                        _add_change(mod_name, 'updated', meta_key)
                
        missing_modules = self.find({'name' : {'$nin' : list(available_modules.keys())}}, read_fields=['name'])
        if missing_modules:
            for mod in missing_modules:
                res.setdefault('removed_modules', []).append(mod['name'])
        
        return res
    
    def _get_module_db_vals(self, module_name, module_info):
        """
        Take values from the module configuration and build the data needed
        for a rev.modules record
        """
        
        return {
            'name' : module_name,
            'module_name' : module_info.get('name', None),
            'module_description' : module_info.get('description', None),
            'module_version' : module_info.get('version', None),
            'depends' : module_info.get('depends', None),
            'auto_install' : module_info.get('auto_install', False),
        }
    
    def _get_module_ids(self):
        """
        Return dictionary mapping module names to database ids
        """
        mod_list = self.find({}, read_fields=['name'])
        res = {}
        for mod in mod_list:
            res[mod['name']] = mod['id']
        return res
         
    def update_module_metadata(self, available_modules):
        """
        Takes a dictionary of module information and updates the
        module information currently held in the database.
        """
        
        module_changes = self.get_module_metadata_changes(available_modules)
        
        if module_changes:
            db_ids = self._get_module_ids()
            
            if 'new_modules'in module_changes:
                for mod_name in module_changes['new_modules']:
                    mod_vals = self._get_module_db_vals(mod_name, available_modules[mod_name])
                    mod_vals['db_version'] = mod_vals['module_version'] 
                    mod_id = self.create(mod_vals)
            
            if 'changed_modules' in module_changes:
                for mod_name in module_changes['changed_modules']:
                    mod_vals = self._get_module_db_vals(mod_name, available_modules[mod_name])
                    self.update([db_ids[mod_name]], mod_vals)
            
            if 'removed_modules' in module_changes and module_changes['removed_modules']:
                del_ids = [db_ids[mod_name] for mod_name in module_changes['removed_modules']]
                self.delete(del_ids)
    
    def schedule_operation(self, operation,  module_names, dependency_stack=[]):
        """
        Schedules the install, update or removal of the specified modules and their dependencies
        
        Operation can be 'install', 'update' or 'remove'
        
        Returns True when done
        """

        def _build_dep_str(mod_name):
            # Return the full dependency path (e.g. revcrm_opportunity -> revcrm_base -> rev_base))
            if not dependency_stack:
                return mod_name
            else:
                return ' -> '.join(dependency_stack) + (', ' + mod_name) if mod_name else ''

        for mod in module_names:
            if mod in dependency_stack:
                raise ValidationError("Circular Module Dependency Detected!: " + _build_dep_str(mod))
        
        mod_data = self.find({'name' : {'$in' : module_names}}, read_fields='*')
        mod_data = dict( [(mod['name'], mod) for mod in mod_data] )
                
        for mod in module_names:
            if mod not in mod_data:
                raise ValidationError("Unknown Module '{}' required by '{}'".format(mod, _build_dep_str('')))
            
            if operation == 'install':
                # If this module is not currently installed, install it!
                if mod_data[mod]['status'] == 'not_installed':
                    self.update([mod_data[mod]['id']], {'status' : 'to_install'})
                # Make sure all current dependencies are installed as well
                if mod_data[mod]['depends']:
                    dstack = dependency_stack.copy()
                    dstack.append(mod)
                    self.schedule_operation('install', mod_data[mod]['depends'], dstack)
            
            elif operation == 'update':
                # if this module is not installed, then we should install it
                if mod_data[mod]['status'] == 'not_installed':
                    self.update([mod_data[mod]['id']], {'status' : 'to_install'})
                    # Make sure all current dependencies are installed as well
                    # (only do this if it was not installed)
                    if mod_data[mod]['depends']:
                        self.schedule_operation('install', mod_data[mod]['depends'], [])
                
                elif mod_data[mod]['status'] == 'installed':
                    self.update([mod_data[mod]['id']], {'status' : 'to_update'})
                    # Make sure all modules that depend on this one are also scheduled for an update
                    dep_mods = self.find({'depends' : mod}, read_fields=['name'])
                    if dep_mods:
                        dstack = dependency_stack.copy()
                        dstack.append(mod)
                        self.schedule_operation('update', [m['name'] for m in dep_mods], dstack)
            
            elif operation == 'remove':
                # If this module is scheduled for install, then just cancel that
                if mod_data[mod]['status'] == 'to_install':
                    self.update([mod_data[mod]['id']], {'status' : 'not_installed'})
                # otherwise mark it for removal, as appropriate
                elif mod_data[mod]['status'] not in ['not_installed', 'to_remove']:
                    self.update([mod_data[mod]['id']], {'status' : 'to_remove'})
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
            mod_ids[mod['status']].append(mod['id'])
        if mod_ids['to_install']:
            self.update(mod_ids['to_install'], {'status' : 'not_installed'})
        if mod_ids['to_update']:
            self.update(mod_ids['to_update'], {'status' : 'installed'})
        if mod_ids['to_remove']:
            self.update(mod_ids['to_remove'], {'status' : 'installed'})
                        
    def install_and_load(self):
        """
        Loads the module hierarchy. If any modules are set to be installed /
        upgraded / removed, do that too!
        """
        
        # Do module removals first
        mods_to_remove = self.find({'status' : 'to_remove'}, read_fields='*')
        if mods_to_remove:
            mods_to_sort = {}
            for mod in mods_to_remove:
                mods_to_sort[mod['name']] = set(mod['depends'])
            mod_remove_order = toposort_flatten(mods_to_sort)
            mod_remove_order.reverse()
            for mod in mod_remove_order:
                self.do_remove(mod)
  
        mods_to_load = self.find({'status' : {'$in' : ['installed','to_install','to_update']}}, read_fields='*')
        if mods_to_load:
            mods_to_sort = {}
            for mod in mods_to_load:
                mods_to_sort[mod['name']] = set(mod['depends'])
            mod_load_order = toposort_flatten(mods_to_sort)
            
            for mod in mod_load_order:
                
                rev.log.info('Loading Module: '+mod)
                
                # Import the module
                m = importlib.import_module(mod)
                
                # Import the module's models (if present)
                has_models = False
                try:
                    m = importlib.import_module(mod+'.models')
                    mpath = m.__path__[0]
                    has_models = True
                except ImportError:
                    pass
                
                if has_models:
                    src_files = os.listdir(mpath)
                    src_files.sort() # make sure theres some kind of determinism for module loading!
                    
                    for src_file in src_files:
                        if src_file == '__init__.py' or src_file[-3:] != '.py':
                            continue
                        m = importlib.import_module(mod+'.models.'+src_file[:-3])
                        
                        for msymbol in dir(m):
                            cls = getattr(m, msymbol)
                            if isinstance(cls, type) and issubclass(cls, RevModel):
    
                                # Instantiate model and add to registry
                                cls(self.registry)
                                        
                self.update_data(mod)
    
    def update_data(self, module_name):
        print('TODO: Update data for module: ', module_name)
    
    def remove_data(self, module_record):
        print('TODO: Remove data for module: ', module_record['name'])
    
    def delete(self, ids, context={}):
        """
        Check that none of the modules we are trying to delete are currently installed!
        """
        inst_mods = self.find({'id' : {'$in' : ids}, 'status' : {'$ne' : 'not_installed'}})
        if inst_mods:
            raise ValidationError('One or more of the modules you are trying to remove is currently installed!')
        
        return super(RevModule, self).delete(ids, context)