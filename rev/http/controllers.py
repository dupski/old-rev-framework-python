
from flask.ext.classy import FlaskView, route
from flask import render_template as flask_render_template
from flask import current_app

class RevHTTPController(FlaskView):
    
    @property
    def _app(self):
        return current_app
        
    def _render_template(self, template_name, **kwargs):
        return flask_render_template(template_name, **kwargs)