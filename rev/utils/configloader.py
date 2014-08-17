
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

aparser.add_argument('-r', '--no-request-log',
            help='Disable HTTP Request Logging',
            dest='log_requests',
            action='store_false',
            default=True,
)

def load_config():
    
    config = {}
    
    args = aparser.parse_args()
    
    if args.configfile:
        rev.log.info('Config File: %s', args.configfile)
        exec(open(args.configfile).read(), {}, config)
    
    config.update(vars(args))

    return config
