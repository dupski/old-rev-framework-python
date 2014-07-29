#!/usr/bin/env node
'use strict';

var express = require('express');
var path = require('path');
var winston = require('winston');

var pkg = require('./package.json');
var cloader = require('./utils/configloader');
var mloader = require('./utils/moduleloader');

exports.config = null;
exports.log = null;
exports.express_app = null;
exports.models = null;
exports.RevModel = require('./core/rev_model').RevModel;

var config = exports.config = cloader.loadConfig();
//console.dir(config);

var log = exports.log = new (winston.Logger)({
	transports: [
	    new (winston.transports.Console)({
	    	timestamp: true,
	    	colorize: true
	    })
	    //new (winston.transports.File)({ filename: 'rev.log' })
    ]
});

log.info('RevFramework v%s Initialising...', pkg.version);
log.info('Config file: %s', config.config);

var models = exports.models = mloader.loadModules();

var express_app = exports.express_app = express();

if (config.log_requests) {
	express_app.use(function(req, res, next) {
	    log.info('[%s] %s %s', req.ip, req.method, req.originalUrl);
	    next();
	});
}

express_app.get('/', function(req, res){
	res.send('Hello World!');
});

express_app.use('/static/', express.static(path.join(__dirname, 'static')));

var server = express_app.listen(config.server_port, config.server_address, function() {
	log.info('Listening on %s port %s.', config.server_address, config.server_port);
});