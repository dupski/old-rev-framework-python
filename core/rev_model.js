var Class = require('../utils/class').Class;
var rev = require('../rev-server');

exports.RevModel = Class.extend({

	_rev_model: true,

	init: function() {
		
		if (!this._name || !this._description) {
			throw new Error('Rev Models must have _name and _description properties defined!');
		}
		
		rev.log.info('Loading Model: %s', this._name);
		
		this._table_name = this._name.replace(/[^A-Z0-9]+/ig, "_");
		
	},

	post_init: function() {
		// Hook run after validation and before application start
	}
	
});