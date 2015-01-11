
from .jinja_funcs import rev_view

def after_app_load(app, prev_mod_info, syncdb):

    javascript = []
    css = []
    for mod_name in app.module_load_order:
        if 'javascript' in app.module_info[mod_name]:
            javascript.extend(app.module_info[mod_name]['javascript'])
        if 'css' in app.module_info[mod_name]:
            css.extend(app.module_info[mod_name]['css'])

    
    @app.context_processor
    def setup_jinja_context():
        return {
            # add rev_view() function to jinja2 context
            'rev_view' : rev_view,
            'js_files' : javascript,
            'css_files' : css,
        }
