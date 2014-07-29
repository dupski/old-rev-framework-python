
var rev = require('../../../rev-server');

exports.RevUser = rev.RevModel.extend({
	_name: 'rev.user',
	_description: 'Rev App User',
	
	_columns: {
		name: 'name field def...',
		email: 'email field def...'
	}
});