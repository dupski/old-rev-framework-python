
var rev = require('../../../rev-server');

exports.RevModelMeta = rev.RevModel.extend({
	_name: 'rev.model',
	_description: 'Rev App Model',
	
	_columns: {
		name: 'name field def...',
	}
});

exports.RevFieldMeta = rev.RevModel.extend({
	_name: 'rev.field',
	_description: 'Rev App Field',
	
	_columns: {
		name: 'name field def...',
	}
});