
import argparse
from .args import BaseArgParser, BaseCommand

class RunServerArgParser(BaseArgParser):

    def __init__(self, app, **kwargs):
        
        class IPAddressValidator(argparse.Action):
            def __call__(self, parser, namespace, values, option_string=None):
                setattr(namespace, self.dest, values)
        
        class PortNumberValidator(argparse.Action):
            def __call__(self, parser, namespace, values, option_string=None):
                setattr(namespace, self.dest, values)
        
        super().__init__(
                usage='%(prog)s runserver [ipaddress] [port] [options]',
                **kwargs)
        
        self.description += '\n\n  runserver - Runs a local test server for your Rev Framework application'
    
        self.add_argument('command', help=argparse.SUPPRESS)
        
        self.add_argument('ipaddress',
                          type=str,
                          nargs='?',
                          action=IPAddressValidator,
                          default=app.settings['DEBUG_SERVER_ADDRESS'],
                          help='Sets the IP Address to run the server on')
        
        self.add_argument('port',
                          type=int,
                          nargs='?',
                          action=PortNumberValidator,
                          default=app.settings['DEBUG_SERVER_PORT'],
                          help='Sets the Port Number to run the server on')

import logging

class RunServerCommand(BaseCommand):
    def run(self, app, args, **kwargs):

        from rev import PKG_NAME, PKG_VERSION

        logging.info('{} v{}'.format(PKG_NAME, PKG_VERSION))

        logging.info("Starting Rev App '{}' ...".format(app.name))
        
        app.init()
        
        app.run(
            host=args.ipaddress,
            port=args.port,
            debug=True,
            use_reloader=False)