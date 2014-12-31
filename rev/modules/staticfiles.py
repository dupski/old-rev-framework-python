
# Utility class to handle static files

import os
from copy import copy

from flask import send_from_directory, abort
from flask.ext.classy import route
from rev.http import RevHTTPController

import logging

class StaticFiles:
    
    def __init__(self, app):
        self.app = app
        self.mod_search_order = copy(app.module_load_order)
        self.mod_search_order.reverse()
    
    def find(self, file_url):
        """
        Return absolute path of matched static file URL
        """
        # latest-loaded module static files have precedence
        # TODO: Check security of this method! (although it should never be used in production)
        for mod in self.mod_search_order:
            filepath = os.path.join(self.app.module_info[mod]['module_path'], 'static', file_url)
            if os.path.exists(filepath):
                return filepath
        return None
    
    def list(self):
        """
        Return list of tuples of (file_url, absolute_path) for all static files
        """
        matched_urls = []
        file_list = []
        for mod in self.mod_search_order:
            staticpath = os.path.join(self.app.module_info[mod]['module_path'], 'static')
            if os.path.exists(staticpath):
                for root, dirs, files in os.walk(staticpath):
                    for filename in files:
                        abs_path = os.path.join(root, filename)
                        # Work out static url from absolute path
                        #TODO: Support winblows
                        file_url = abs_path[len(staticpath)-6:]
                        if file_url not in matched_urls:
                            file_list.append((file_url, abs_path))
                            matched_urls.append(file_url)
        return file_list

class StaticFilesEndpoint(RevHTTPController):
    route_base = '/'
 
    @route('/static/<path:file_url>')
    def static_file(self, file_url):
        filepath = self._app.staticfiles.find(file_url)
        if filepath:
            #logging.debug("Serving '{}' from '{}'".format(file_url, filepath))
            filedir, filename = os.path.split(filepath)
            return send_from_directory(filedir, filename)
        abort(404)