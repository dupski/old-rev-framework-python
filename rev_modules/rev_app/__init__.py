
from .jinja_funcs import rev_view

def after_app_load(app, prev_mod_info, syncdb):

    # add rev_view() function to jinja2 context
    @app.context_processor
    def setup_rev_view_jinja_function():
        return {'rev_view' : rev_view}