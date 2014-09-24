
import rev
from rev.core.models import RevModelRegistry, RevModel, registry
from rev.core.modules import RevModule

import os, sys
import imp

def load_modules(db):
	
	available_modules = {}
	
	# Check specified module paths and collect metadata
	rev.log.info("Module Path: " + rev.config['module_path'])

	mod_path_list = rev.config['module_path'].split(',')
	for mod_path in mod_path_list:
		if not os.path.isdir(mod_path):
			raise Exception("Module Path '{}' is not a directory!".format(mod_path))
		
		mod_folders = [name for name in os.listdir(mod_path)
						if os.path.isdir(os.path.join(mod_path, name))]
		for mod_folder in mod_folders:
			try:
				mod_info = imp.find_module(mod_folder)
				rev.log.warning("Module '{}' overwrites existing module at '{}'".format(mod_folder, mod_info[1]))
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
	
	# Module paths validated. Add them to python path
	for mod_path in mod_path_list:
		sys.path.insert(0, mod_path)
				
	# Create Model Registry
	registry = RevModelRegistry(db)
	rev.core.models.registry = registry

	# Initialise the RevModule model
	module_obj = RevModule(registry)

	# Get differences between database list of modules and installed modules
	rev.log.info("Checking Module Metadata is up-to-date...")
	module_changes = module_obj.get_module_metadata_changes(available_modules)
	
	# Prompt user to update database metadata if necessary
	if module_changes:
		print('The following module changes were detected:')
		if 'new_modules' in module_changes:
			print('NEW MODULES: ', ', '.join(module_changes['new_modules']))
		if 'removed_modules' in module_changes:
			print('REMOVED MODULES: ', ', '.join(module_changes['removed_modules']))
		if 'changed_modules' in module_changes:
			print('CHANGED MODULES: ')
			for mod_name, mod_change in module_changes['changed_modules'].items():
				print('  MODULE: ', mod_name)
				if 'updated' in mod_change:
					print('    UPDATED KEYS: ', ', '.join(mod_change['updated']))
		
		response = ''
		while response not in ['y','n']:
			response = input("Do you want to update the module metadata in database '{}'? (y/n): ".format(db.name)).lower()
		
		if response == 'n':
			print('Cannot continue without up-to-date module metadata.')
			sys.exit(1)
		
		module_obj.update_module_metadata(available_modules)
	
	# Check for modules set to 'auto_install' that are not installed
	mods_to_auto_install = module_obj.find({'auto_install' : True, 'status' : 'not_installed'}, read_fields=['name'])
	
	if mods_to_auto_install:

		mod_names = [mod['name'] for mod in mods_to_auto_install]

		print('The following modules are set to auto-install and are not currently installed:')
		print('  ' + ', '.join(mod_names))

		response = ''
		while response not in ['y','n']:
			response = input("Do you want to install them? (y/n): ").lower()
		
		if response == 'y':
			module_obj.schedule_operation('install', mod_names)
	
	# Check for any module changes specified on the command line
	if rev.config['modules_to_install']:
		module_obj.schedule_operation('install', rev.config['modules_to_install'].split(','))
	if rev.config['modules_to_update']:
		module_obj.schedule_operation('update', rev.config['modules_to_update'].split(','))
	if rev.config['modules_to_remove']:
		module_obj.schedule_operation('remove', rev.config['modules_to_remove'].split(','))
		
	# Scan for any scheduled module changes and prompt the user whether to go ahead
	scheduled_operations = module_obj.find({'status' : {'$in' : ['to_install', 'to_update', 'to_remove']}}, read_fields=['name','status'])
	
	if scheduled_operations:
		ops = {
			'to_install' : [],
			'to_update' : [],
			'to_remove' : [],
		}
		for op in scheduled_operations:
			ops[op['status']].append(op['name'])
		
		if ops['to_install']:
			print('The following modules are about to be INSTALLED:')
			print('  ' + ', '.join(ops['to_install']))
		if ops['to_update']:
			print('The following modules are about to be UPDATED:')
			print('  ' + ', '.join(ops['to_update']))
		if ops['to_remove']:
			print('The following modules are about to be REMOVED:')
			print('  ' + ', '.join(ops['to_remove']))
				
		response = ''
		while response not in ['y','n']:
			response = input("Do you want to continue? (y/n): ").lower()
	
		if response == 'n':
			
			response = ''
			while response not in ['y','n']:
				response = input("Do you want to cancel the scheduled install/update/remove operations? (y/n): ").lower()
		
			if response == 'y':
				module_obj.cancel_scheduled_operations()
			else:
				print("Cannot continue without completing installation or cancelling.")
				sys.exit(1)

	module_obj.install_and_load()

	return registry
