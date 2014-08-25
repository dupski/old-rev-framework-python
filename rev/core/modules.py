
from rev.core.models import RevModel
from rev.core import fields
from rev.core.translations import translate as _

MODULE_STATUSES = [
    ('not_installed', _('Not Installed')),
    ('to_install', _('To Be Installed')),
    ('installed', _('Installed')),
    ('to_upgrade', _('To Be Upgraded')),
]

class RevModules(RevModel):

    _name = 'rev.modules'
    _description = 'Rev Module Information'
    
    name = fields.TextField(_('Module Package Name'))
    module_name = fields.TextField(_('Module Name'))
    module_description = fields.TextField(_('Description'), required=False)
    module_version = fields.TextField(_('Module Version'))
    db_version = fields.TextField(_('Installed Version'))
    status = fields.SelectionField(_('Status'), default_value='not_installed')
    depends = fields.MultiSelectionField(_('Dependancies'), required=False)
    auto_install = fields.BooleanField(_('Automatically Installed?'))
    
    _unique = ['name']
        
    def get_module_metadata_changes(self, available_modules):
        """Takes a dictionary of module information and compares it to the
        module information currently held in the database.
        
        Returns a dictionary with the following keys (if they apply):
        
         - 'new_modules' - list of module names that do not exist in the database
         - 'changed_modules' - dictionary of module name -> list of changes
         - 'removed_modules' - list of modules that do not exist on disk
        """
        res = {}
                
        for mod_name in available_modules:
            db_mod_info = self.find({'name' : mod_name})
            
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
                    
                    if meta_key not in db_mod_info:
                        _add_change(mod_name, 'new', '{}: {}'.format(meta_key, meta_value))
                    
                    elif meta_value != db_mod_info[meta_key]:
                        _add_change(mod_name, 'updated', '{}: {}'.format(meta_key, meta_value))
                
                for key in db_mod_info:
                    if key not in available_modules[mod_name] and key not in  ['_id', 'status', 'db_version', 'module_version', 'module_name', 'module_description']:
                        _add_change(mod_name, 'deleted', str(key))
                
        missing_modules = self.find({'name' : {'$nin' : list(available_modules.keys())}}, read_fields=['name'])
        if missing_modules:
            for mod in missing_modules:
                res.setdefault('removed_modules', []).append(mod['name'])
        
        return res
    
    def _get_module_db_vals(self, module_name, module_info):
        """Take values from the module configuration and build the data needed
        for a rev.modules record"""
        
        return {
            'name' : module_name,
            'module_name' : module_info.get('name', None),
            'module_description' : module_info.get('description', None),
            'module_version' : module_info.get('version', None),
            'depends' : module_info.get('depends', None),
            'auto_install' : module_info.get('auto_install', False),
        }
         
    def update_module_metadata(self, available_modules):
        """Takes a dictionary of module information and updates the
        module information currently held in the database.
        """
        
        module_changes = self.get_module_metadata_changes(available_modules)
        
        if module_changes:
            if 'new_modules'in module_changes:
                for mod_name in module_changes['new_modules']:
                    mod_vals = self._get_module_db_vals(mod_name, available_modules[mod_name])
                    mod_vals['db_version'] = mod_vals['module_version'] 
                    mod_id = self.create(mod_vals)
                    
                    print(mod_id)