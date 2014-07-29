var Class = require('../utils/class').Class;
var rev = require('../rev-server');

exports.RevModelRegistry = Class.extend({
	
	init: function() {
		this._models = {};
	},

	set: function(modelName, objectInstance) {
		this._models[modelName] = objectInstance;
	},
	
	get: function(modelName) {
		if (!this._models[modelName]) {
			throw new Error("Model '" + modelName + "' has not been defined!");
		}
		else {
			return this._models[modelName];
		}
	},
	
	validate: function() {
		// TODO: Check referential integrity between objects
	}
	
});