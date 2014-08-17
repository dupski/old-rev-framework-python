
var rev = require('../../../rev-server');

exports.RevModule = rev.RevModel.extend({
	_name: 'rev.module',
	_description: 'Rev App Module',
	
	_columns: {
		name: 'name field def...',
	}
});