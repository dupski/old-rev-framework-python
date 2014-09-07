
from flask import Flask, url_for
from flask.ext.classy import FlaskView, route
from flask import render_template as f_render_template
import jinja2

import rev

http_app = None
started = False

class RevHTTP(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        block_start_string='@{%',
        block_end_string='%}',
        variable_start_string='@{{',
        variable_end_string='}}',
        comment_start_string='@{#',
        comment_end_string='#}',
    ))
    
    def __init__(self, *args, **kwargs):
        return super(RevHTTP, self).__init__('rev', *args, **kwargs)

class RevHTTPController(FlaskView):
        
    def _render_template(self, template_name, **kwargs):
        test = {
            'name' : 'Rev Framework Application',
        }
        return f_render_template(template_name, app=test, **kwargs)

# Server Control Functions
def init(config):
    global http_app
    http_app = RevHTTP()

_template_paths = []

def register_template_path(template_path):
    global _template_paths
    _template_paths.append(template_path)
    
def start(config):
    global started
    global _template_paths
    
    tpl_loaders = [http_app.jinja_loader]        
    for tpl_path in _template_paths:
        tpl_loaders.append(jinja2.FileSystemLoader(tpl_path))
    tpl_loaders.reverse() # Last imported module should take precedence
        
    http_app.jinja_loader = jinja2.ChoiceLoader(tpl_loaders)

    rev.log.debug('REGISTERED HTTP ENDPOINTS:')
    for rule in http_app.url_map.iter_rules():
        rev.log.debug('  '+rule.rule+' => '+rule.endpoint)

    started = True
    
    http_app.run(
        host=config['server_address'],
        port=config['server_port'],
        debug=True,
        use_reloader=False)
