
import argparse
from .args import BaseArgParser, BaseCommand

class SyncDBArgParser(BaseArgParser):

    def __init__(self, app, **kwargs):
        
        super().__init__(
                usage='%(prog)s syncdb [options]',
                **kwargs)
        
        self.description += '\n\n  syncdb - Synchronise application database metadata'
    
        self.add_argument('command', help=argparse.SUPPRESS)

import logging

class SyncDBCommand(BaseCommand):
    def run(self, app, args, **kwargs):

        from rev import PKG_NAME, PKG_VERSION

        logging.info('{} v{}'.format(PKG_NAME, PKG_VERSION))

        logging.info("Running Sync DB for Rev App '{}' ...".format(app.name))
        
        app.init(syncdb=True)

        logging.info('Sync DB Completed.')
