
import logging
from .viewloader import load_views

def after_app_load(app, prev_mod_info):
    logging.info("Loading Views for Running Modules...")
    app.views = load_views(app)
    