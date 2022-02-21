import http.server 
from urllib.parse import parse_qs


PORT = 2453 #Some Random port numbers
FILE = "auth_code.file"
class PySpoyServer(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        site = ""
        if(self.path[0] == "/"):
            payload = parse_qs(self.path)
            if "/?code" in payload and "state"in payload:
                with open(FILE, "w") as f:
                    f.write(payload["/?code"][0])
                    #f.write(payload["state"][0])
                site = "You can close this window"
                self.send_response(200)

            else:
                self.send_response(418)
                site = "Failed to read your authentication code!"
                print("Failure to read the code")
        else:
            site = "Spotify is being weird and send a wrong redirect"
            self.send_response(404)
            print("Not an end point!")
        self.end_headers()
        self.wfile.write(bytes(site, "utf-8"))

httpd = http.server.HTTPServer(("localhost", PORT), PySpoyServer)
def runServer():
    httpd.serve_forever()

def closeServer():
    httpd.shutdown()
