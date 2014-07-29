
var rev = require('../../../rev-server');

exports.RevView = rev.RevModel.extend({
	_name: 'rev.view',
	_description: 'Rev App View',

	_view_types: [
		['form', 'Form View'],
		['list', 'List View'],
	],

	_columns: {
		name: 'name field def...',
		email: 'email field def...'
	}
});