import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

root_path = '/home/sac/test-stac'
os.chdir(root_path)

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super(CORSRequestHandler, self).end_headers()


with HTTPServer(('localhost', 5555), CORSRequestHandler) as httpd:
    httpd.serve_forever()
