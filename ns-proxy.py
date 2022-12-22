from kubernetes import client, config
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import requests
import threading
import time

def forward(method, url, headers, data):
    try:
        if method == "GET":
            requests.get(url, headers=headers, timeout=2)
        elif method == "POST":
            requests.post(url, headers=headers, timeout=2, data=data)
    except Exception as e:
        print("unable to send to", url, e)

class MyServer(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.ns_list = []
        self.last_updated = 0
        self.targetSvc = kwargs.pop('targetSvc')

    def __call__(self, *args, **kwargs):
        """ Handle a request """
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()

    def get_ns_list(self):
        if time.time() > self.last_updated + 15:
            print("updating ns list")
            new_list = []
            ret = v1.list_service_for_all_namespaces(watch=False)
            for i in ret.items:
                if i.metadata.name == targetSvc:
                    new_list.append(i.metadata.namespace)
            self.ns_list = new_list
            self.last_updated = time.time()
        return self.ns_list

    def handle_request(self):
        for fh in [ "Host" ]:
            del self.headers[fh]

        method = self.command
        path = self.path
        headers = self.headers
        data = None

        if method == "POST":
            # cannot handle chunked
            data = self.rfile.read(int(self.headers['Content-Length']))

        self.send_response(200)
        self.end_headers()

        for ns in self.get_ns_list():
            url = "http://%s.%s.svc.cluster.local%s" % (self.targetSvc, ns, path)
            threading.Thread(target=forward, args=(method, url, headers, data,)).start()

if __name__ == "__main__":        
    config.load_incluster_config()
    v1 = client.CoreV1Api()

    targetSvc = os.environ['TARGET_SERVICE']
    listenIp = os.environ.get('LISTEN_IP', '0.0.0.0')
    listenPort = int(os.environ.get('LISTEN_PORT', '8080'))

    handler = MyServer(targetSvc=targetSvc)
    webServer = HTTPServer((listenIp, listenPort), handler)
    print("Server started http://%s:%s" % (listenIp, listenPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")

