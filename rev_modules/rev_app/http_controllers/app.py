
from rev.http import RevHTTPController
from flask import render_template, current_app, request, abort

class RevAppHTTPController(RevHTTPController):
    route_base = '/'

    def index(self):
        return render_template('index.html')
    
    def view(self, module, view_id):
        view = current_app.cache.get('/view'+request.path)
        if not view:
            view = current_app.registry.get('View').get_rendered_view(module, view_id)
            if not view:
                view = '404'
            current_app.cache.set('/view'+request.path, view)
        if view == '404':
            abort(404)
        return view
        