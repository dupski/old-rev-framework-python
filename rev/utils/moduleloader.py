
import rev
from rev.core.models import RevModelRegistry, RevModel
from rev.core.modules import RevModules

import os, sys
import imp

from toposort import toposort_flatten

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
				raise Exception("Module '{}' __rev__.conf does not contain any dependancy information".format(mod_folder))
			
			available_modules[mod_folder] = module_info
	
	# Module paths validated. Add them to python path
	for mod_path in mod_path_list:
		sys.path.insert(0, mod_path)
				
	# Create Model Registry
	registry = RevModelRegistry(db)

	# Initialise the RevModule model
	module_obj = RevModules(registry)

	known_modules = module_obj.find(read_fields=['name','status'])
	known_module_info = {}
	for mod in known_modules:
		known_module_info[mod['name']] = {'_id' : mod['_id'], 'status' : mod['status']}
		
# 	
# 	available_modules = []
# 
# 	for mod_path in mod_path_list:
# 			
# 			rev.log.info('Loading Module: %s', mod_folder)
# 			
# 			if os.path.isdir(os.path.join(mod_path, mod_folder, 'models')):
# 				rev.log.info('Loading Models...')

	return registry

class ModuleSet():
	
	def __init__(self, available_modules):
		self.available_modules = available_modules
		self.modules = {}
	
	def add_module(self, name, parent_stack=[]):
		if name not in self.available_modules:
			if parent_stack:
				raise Exception("Module '{}' required by '{}' cannot be found!".format(name, parent_stack[-1]))
			else:
				raise Exception("Module '{}' cannot be found!".format(name))
		if name not in self.modules:
			self.modules[name] = self.available_modules[name]
			for dep in self.modules[name]['depends']:
				pass
			