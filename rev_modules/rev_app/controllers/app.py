
from rev.http import RevHTTPController

class RevAppHTTPController(RevHTTPController):
    route_base = '/'

    def index(self):
        app = self._app        
        return self._render_template('index.html', app=app)
