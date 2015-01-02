
from rev.http import RevHTTPController

class RevAppHTTPController(RevHTTPController):
    route_base = '/'

    def index(self):
        return self._render_template('index.html')
