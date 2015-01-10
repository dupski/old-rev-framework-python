
from flask import current_app
from jinja2.utils import Markup

def rev_view(view_id):
    """
    rev_view() function for jinja2 that inserts a rendered rev-view
    view_id should be in the format <module>.<view_id>
    """
    view_id_str = str(view_id)
    view_id = view_id_str.split('.')
    if len(view_id) != 2:
        raise Exception("Invalid view_id specified for rev_view(). Should be in the format <module>.<view_id>.")

    rendered_html = current_app.registry.get('View').get_rendered_view(view_id[0], view_id[1])

    if rendered_html is None:
        raise Exception("Could not find the specified rev-view: '{}'".format(view_id_str))
    
    return Markup(rendered_html)
