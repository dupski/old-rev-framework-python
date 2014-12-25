
from flask.ext.classy import FlaskView, route
from flask import render_template as flask_render_template

class RevHTTPController(FlaskView):
        
    def render_template(self, template_name, **kwargs):
        test = {
            'name' : 'Rev Framework Application',
        }
        return flask_render_template(template_name, **kwargs)