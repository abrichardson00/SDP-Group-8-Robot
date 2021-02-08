import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO

# Hosts a web server at http://localhost:8000/ 
# Upon recieving POST requests, it processes the key-value pairs of data attached, and then can do stuff
# For now it just prints text that confirms the communication works as expected 
# - but I guess these sections are where we let the rest of the python functionality take over 
# After doing these things, it also sends a response back to the request sender (the App.java file then prints this response as a confirmation)

class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def _html(self, message):
        """This just generates an HTML document that includes `message`
        in the body. Override, or re-write this do do more interesting stuff.
        """
        content = f"<html><body><h1>{message}</h1></body></html>"
        return content.encode("utf8")  # NOTE: must return a bytes object!

    def do_GET(self):
        self._set_headers()
        self.wfile.write(self._html("hi!"))

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        # Doesn't do anything with posted data
        #self._set_headers()
        #self.wfile.write(self._html("POST!"))
        
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        
        ### make the robot do a thing!
        self.handle_what_the_robot_does(str(body))

        ### send a response, confirm 
        ### when the app recieves the confirmation it could do something
        self.send_response(200)
        self.end_headers()
        response = BytesIO()
        response.write(b'This is POST request. ')
        response.write(b'Received: ')
        response.write(body)
        self.wfile.write(response.getvalue())



    def handle_what_the_robot_does(self,input_text):
        action = ""
        tray = ""
        text = ""
        # given input_text, we remove outer ' and the "b" at the start
        for key_value_pair in input_text.replace('b\'','').replace('\'','').split('&'): # (there's probably a better way to do this)
            key, value = key_value_pair.split('=')
            if (key=="action"):
                action = value
            if (key=="tray"):
                tray = value
            if (key=="text"):
                text = value.replace('+', ' ').replace("%2C",',') # spaces in the text get formatted to '+' signs in the request - lets turn them back to spaces
        
        ### now perhaps we have action = "bring", tray = "A"
        ### or action = "update_info", tray = "B", text = "bananas"
        ### or action = "store" (nothing else matters, can only store current open tray)
        ### etc...

        ### now these 'actions' could correspond to calling the appropriate functions elsewhere
        ### perhaps elsewhere we have a robot class and we call Robot.do_thing(action, tray, text) or something like that

        if action=="bring":
            print("I'm gonna bring tray " + tray + "!")
        elif action=="store":
            print("I'm gonna store the current open tray")
        elif action=="update_info":
            print("Updating the description of tray " + tray + " to " + "\""+ text + "\"")
        else:
            print("invalid request?")


def run(server_class=HTTPServer, handler_class=S, addr="localhost", port=8000):
    server_address = (addr, port)
    httpd = server_class(server_address, handler_class)

    print(f"Starting httpd server on {addr}:{port}")
    httpd.serve_forever()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run a simple HTTP server")
    parser.add_argument(
        "-l",
        "--listen",
        default="localhost",
        help="Specify the IP address on which the server listens",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Specify the port on which the server listens",
    )
    args = parser.parse_args()
    run(addr=args.listen, port=args.port)
