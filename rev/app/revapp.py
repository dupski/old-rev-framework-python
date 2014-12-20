
from flask import Flask
import logging
from pprint import pformat

# Main RevFramework Application object

class RevApp(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        block_start_string='@{%',
        block_end_string='%}',
        variable_start_string='@{{',
        variable_end_string='}}',
        comment_start_string='@{#',
        comment_end_string='#}',
    ))
    
    def __init__(self, app_name, settings, *args, **kwargs):
        
        # Load settings module into self.settings
        self.name = app_name
        self.settings = {}
        for setting in dir(settings):
            if setting.isupper():
                self.settings[setting] = getattr(settings, setting)
        
        # Hardcode the flask import_name to 'rev'. Template and static file paths are sorted out later.
        return super().__init__('rev', *args, **kwargs)
