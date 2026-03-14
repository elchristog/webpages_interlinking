import http.server
import socketserver
import os
import sys

PORT = 8080
DIRECTORY = "proyectos"

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def list_directory(self, path):
        # Base list directory plus some flavor to help navigate the webs
        try:
            list = os.listdir(path)
        except OSError:
            self.send_error(404, "No access to this directory")
            return None
        list.sort(key=lambda a: a.lower())
        
        # We want to show the links to the generated 'webs' folders if they exist
        output = f'<html><head><title>Visor de Webs - PBN</title><style>body {{ font-family: sans-serif; background: #121212; color: #eee; padding: 20px; }} a {{ color: #4CAF50; }} ul {{ list-style: none; padding: 0; }} li {{ margin-bottom: 10px; padding: 10px; background: #1e1e1e; border-radius: 5px; }} h1 {{ color: #fff; }}</style></head><body><h1>Visor de Proyectos y Sitios Espejo</h1><ul>'
        
        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            
            # Special logic: if it's a project folder, show it. If it's a 'webs' folder, it's what we want.
            output += f'<li><a href="{linkname}">{displayname}</a></li>'
            
        output += "</ul></body></html>"
        encoded = output.encode('utf-8', 'surrogateescape')
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        DIRECTORY = sys.argv[1]

    os.chdir(DIRECTORY)
    Handler = MyHandler

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Visor de webs corriendo en http://localhost:{PORT}")
        print(f"Sirviendo desde: {os.path.abspath(DIRECTORY)}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nApagando servidor...")
            httpd.server_close()
