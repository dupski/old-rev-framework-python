
from rev.http import RevHTTPController
from rev_app.view import get_view
from flask import render_template, abort

class RevAppHTTPController(RevHTTPController):
    route_base = '/'

    def index(self):
        return render_template('index.html')
    
    def view(self, module, view_id):
        view = get_view(module, view_id)
        if view is None:
            abort(404)
        return view
