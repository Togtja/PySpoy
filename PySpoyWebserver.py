import http.server


PORT = 2453 #Some Random port numbers
FILE = "auth_code.file"
class PySpoyServer(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        site = ""
        if(self.path[0] == "/"):
            index = self.path.find("code=")
            if index != -1:
                code=self.path[index+5:]
                with open(FILE, "w") as f:
                    f.write(code)
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
