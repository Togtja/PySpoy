import http.server


PORT = 2453 #Some Random port numbers
FILE = "auth_code.file"
class PySpoyServer(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if(self.path[0] == "/"):
            index = self.path.find("code=")
            if index != -1:
                code=self.path[index+5:]
                with open(FILE, "w") as f:
                    f.write(code)

                self.send_response(200)
                self.end_headers()
            else:
                print("Failure to read the code")
        else:
            print("Not an end point!")

httpd = http.server.HTTPServer(("localhost", PORT), PySpoyServer)
def runServer():
    httpd.serve_forever()

def closeServer():
    httpd.shutdown()
