from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import urllib2
import getopt
import sys
import os
from lfu import Cache

# max available size of local disk
# 1024 * 1024 * 10 - 500 * 1024
MAX_SIZE = 9973760
# MAX_SIZE = 600000

class MyHTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, cache, origin, *args):
        self.origin = origin
        self.cache = cache
        BaseHTTPRequestHandler.__init__(self, *args)

    def do_GET(self):
        # If request page in not in the cache
        if not self.cache.contains(self.path):
            self.download_from_origin()
            print "[DEBUG]inserted into cache"
            print "cache:", self.cache
        else:
            self.cache.access(self.path)
            print "[DEBUG]incremented frequency in cache"
            print "cache:", self.cache

        # Read cached file from local file
        with open(os.getcwd() + self.path) as request_page:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(request_page.read())

    def download_from_origin(self):
        print "[DEBUG]downloading from origin"
        try:
            if len(self.origin.split(':')) == 1:
                self.origin += ':8080'
            request = 'http://' + self.origin + self.path
            print "request:", request
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as he:
            self.send_error(he.code, he.reason)
            return
        except urllib2.URLError as ue:
            self.send_error(ue.reason)
            return
        else:
            self.save_to_cache(self.path, response)

    def save_to_cache(self, path, response):
        print "[DEBUG]saving to cache"
        filename = os.getcwd() + self.path
        directory = os.path.dirname(filename)

        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except:
                print "Can not make dir, exceed memory size limit"

        try:
            response_size = int(len(response.read()))
            # Insert the new path in LFU cache
            if response_size <= MAX_SIZE:
                                self.cache.insert(self.path, response_size)
            f = open(filename, 'w')
            f.write(response.read())
        # Handle write exception
        except IOError as ue:
            print 'Can not write, Wiki folder exceed memory size limit'

def get_information(argv):
    if (len(argv) != 5):
        sys.exit('Usage: %s -p <port> -o <origin>' % argv[0])

    (port_num, origin) = (0, '')
    options, arguments = getopt.getopt(argv[1:], 'p:o:')
    for opt, arg in options:
        if opt == '-p':
            port_num = int(arg)
        elif opt == '-o':
            origin = arg
        else:
            sys.exit('Usage: %s -p <port> -o <origin>' % argv[0])
    return port_num, origin

if __name__ == '__main__':
    (port_num, origin) = get_information(sys.argv)
    print 'max size:', MAX_SIZE
    cache = Cache(MAX_SIZE)
    print 'initialize cache here'
    print 'cache:', cache

    def handler(*args):
        MyHTTPHandler(cache, origin, *args)

    httpserver = HTTPServer(('', port_num), handler)
    httpserver.serve_forever()