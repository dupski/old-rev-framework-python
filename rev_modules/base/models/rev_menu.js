
var rev = require('../../../rev-server');

exports.RevMenu = rev.RevModel.extend({
	_name: 'rev.menu',
	_description: 'Rev App Menu',
	
	_columns: {
		name: 'name field def...',
		parent_id: 'parent field def...',
	}
});
