
var rev = require('../rev-server');
var RevModelRegistry = require('../core/rev_model_registry').RevModelRegistry;

var fs = require('fs');
var path = require('path');

exports.loadModules = function() {
	// Load modules and return a RevModelRegistry
	
	var registry = new RevModelRegistry();	
	
	// TODO: Get modules from database
	moduleLoadList = ['base'];
	
	mod_path_list = rev.config.module_path.split(',');

	for (var i=0; i<mod_path_list.length; i++) {
    	var mod_folders = [];
    	try {
    		mod_folders = fs.readdirSync(mod_path_list[i]);
    	}
    	catch (err) {
    		throw new Error("Module Path '" + mod_path_list[i] + "' is invalid!");
    	}
    	for (var j=0; j<mod_folders.length; j++) {
    		var mod_path = path.join(mod_path_list[i], mod_folders[j])    		
    		if (fs.statSync(mod_path).isDirectory()) {
    			rev.log.info('Loading Module: %s', mod_folders[j]);
    			if (fs.statSync(mod_path + '/models').isDirectory()) {
    				rev.log.info('Loading Models...');
    		    	var model_files = fs.readdirSync(mod_path + '/models');
    		    	for (var k=0; k<model_files.length; k++) {
    		    		var mod_file = mod_path+'/models/'+model_files[k];
    		    		if (fs.statSync(mod_file).isFile()) {
    		    			var mod = require(mod_file);
    		    			for (prop in mod) {
    		    				var model = new mod[prop]();
    		    				if (model._rev_model && model._name) {
    		    					registry.set(model._name, model);
    		    				}
    		    			}
    		    		}
    		    	}
    			}
    		}
    	}
	}
	
	return registry;
}
