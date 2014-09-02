
import os
import argparse

import rev
from rev.core import PKG_NAME, PKG_VERSION

aparser = argparse.ArgumentParser(
                    description='{} v{}'.format(PKG_NAME, PKG_VERSION),
                    add_help=True,
)

aparser.add_argument('-c', '--config', 
            help='Specify configuration file to use',
            dest='configfile',
            default=os.path.join(os.getcwd(), 'revserver.conf'))

aparser.add_argument('-i', '--install',
            help='Specify a comma-seperated list of modules to install',
            dest='modules_to_install',
            default=None)

aparser.add_argument('-u', '--update',
            help='Specify a comma-seperated list of modules to update',
            dest='modules_to_update',
            default=None)

aparser.add_argument('-r', '--remove',
            help='Specify a comma-seperated list of modules to remove',
            dest='modules_to_remove',
            default=None)

def load_config():
    
    config = {}
    
    args = aparser.parse_args()
    
    if args.configfile:
        rev.log.info('Config File: %s', args.configfile)
        exec(open(args.configfile).read(), {}, config)
    
    config.update(vars(args))

    return config
