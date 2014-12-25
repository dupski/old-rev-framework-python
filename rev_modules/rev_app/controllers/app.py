
from rev.http import RevHTTPController

class RevAppHTTPController(RevHTTPController):
    route_base = '/'

    def index(self):
        return self.render_template('base.html')
    
    def mytest(self):
        return "self = " + str(dir(self))