
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
    
    name = fields.TextField(_('Module Name'))
    description = fields.TextField(_('Description'))
    db_version = fields.TextField(_('Installed Version'))
    module_version = fields.TextField(_('Module Version'))
    status = fields.SelectionField(_('Status'))
    
    _unique = ['name']
    
    def get_module_meta_changes(self, available_modules):
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
                def _add_change(module_name, change_type, change_desc):
                    res.setdefault('changed_modules', {}).setdefault(module_name, {})[change_type] = change_desc

                for meta_key, meta_value in available_modules[mod_name].items():
                    
                    if meta_key not in db_mod_info:
                        _add_change(mod_name, 'new', '{}: {}'.format(meta_key, meta_value))
                    
                    elif meta_value != db_mod_info[meta_key]:
                        _add_change(mod_name, 'updated', '{}: {}'.format(meta_key, meta_value))
                
                for key in db_mod_info:
                    if key not in available_modules[mod_name]:
                        _add_change(mod_name, 'deleted', str(key))
        
        missing_modules = self.find({'name' : {'$nin' : list(available_modules.keys())}}, read_fields=['name'])
        if missing_modules:
            for mod in missing_modules:
                res.setdefault('removed_modules', []).append(mod['name'])
        
        return res
                
                