#!/usr/bin/env python3

# Configure Base Import Path
import os,sys
basedir = os.path.dirname(__file__)
sys.path.insert(0, basedir)

# Configure Logging
import logging
from colorlog import ColoredFormatter

console_log = logging.StreamHandler()
console_log.setFormatter(ColoredFormatter(
    "%(asctime)s [%(log_color)s%(levelname)s%(reset)s] %(message)s",
))

logging.basicConfig(level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[#log.FileHandler("revserver.log"),
            console_log])

import rev
rev.log = logging

# Initialise Application
from rev.core import PKG_NAME, PKG_VERSION
from rev.utils import configloader, moduleloader

rev.log.info('{} v{} Initialising...'.format(PKG_NAME, PKG_VERSION))

rev.config = configloader.load_config()

# TODO: Connect to database
rev.log.info("Database Server: {}:{}".format(rev.config['db_host'], rev.config['db_port']))
rev.log.info("Database Name: {}".format(rev.config['db_name']))

from pymongo import MongoClient
dbclient = MongoClient(rev.config['db_host'], rev.config['db_port'])
db = dbclient[rev.config['db_name']]

rev.registry = moduleloader.load_modules(db)