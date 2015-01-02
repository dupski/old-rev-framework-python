
import logging
from .rev_view import load_views, rev_view

def after_app_load(app, prev_mod_info):
    logging.info("Loading Views for Running Modules...")
    app.views = load_views(app)
    
    # add rev_view() function to jinja2 context
    
    @app.context_processor
    def rev_view_jinja_function():
        return {'rev_view' : rev_view}