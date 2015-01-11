
from .jinja_funcs import rev_view
import os

def _expand_wildcard_path(module_path, path, file_ext):
    res = []
    for root, dirnames, filenames in os.walk(os.path.join(module_path, path)):
        for filename in filenames:
            if filename[-(len(file_ext)):] == file_ext:
                full_path = os.path.join(root, filename)
                res.append(full_path[len(module_path)+1:])
    return res

def after_app_load(app, prev_mod_info, syncdb):

    javascript = []
    css = []
    for mod_name in app.module_load_order:
        if 'javascript' in app.module_info[mod_name]:
            for js_path in app.module_info[mod_name]['javascript']:
                if js_path[-1] == '*':
                    javascript.extend(_expand_wildcard_path(
                                        app.module_info[mod_name]['module_path'],
                                        js_path[0:-1],
                                        '.js'))
                else:
                    javascript.append(js_path)
        if 'css' in app.module_info[mod_name]:
            for css_path in app.module_info[mod_name]['css']:
                if css_path[-1] == '*':
                    css.extend(_expand_wildcard_path(
                                        app.module_info[mod_name]['module_path'],
                                        css_path[0:-1],
                                        '.css'))
                else:
                    css.append(css_path)
    
    @app.context_processor
    def setup_jinja_context():
        return {
            # add rev_view() function to jinja2 context
            'rev_view' : rev_view,
            'js_files' : javascript,
            'css_files' : css,
        }
