
var _ = require('underscore');
var ArgumentParser = require('argparse').ArgumentParser;
var path = require('path');
var pkg = require('../package.json');

var parser = new ArgumentParser({
  version: pkg.version,
  addHelp: true,
  description: pkg.description
});

parser.addArgument(['-c','--config'], {
	help: 'Specify configuration file to use',
	dest: 'config',
	defaultValue: path.join(__dirname, '..', 'config.js')
});

parser.addArgument(['-r','--no-request-log'], {
	help: 'Disable HTTP Request Logging',
	dest: 'log_requests',
	action: 'storeFalse',
	defaultValue: true
});

exports.loadConfig = function() {
	var args = parser.parseArgs();	
	var config = require(args['config']).config;
	return _.extend(config, args);
}
