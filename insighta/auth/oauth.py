import base64
import hashlib
import secrets
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from urllib.parse import urlparse, parse_qs
import requests


class OAuthHandler:
    def __init__(self, client_id, redirect_uri, backend_url):
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.backend_url = backend_url
        self.state = None
        self.code_verifier = None
        self.code_challenge = None
        self.auth_code = None
        self.callback_received = False

    def generate_pkce(self):
        self.state = secrets.token_urlsafe(32)
        self.code_verifier = secrets.token_urlsafe(32)
        code_challenge_hash = hashlib.sha256(self.code_verifier.encode()).digest()
        self.code_challenge = base64.urlsafe_b64encode(code_challenge_hash).decode().rstrip("=")

    def get_auth_url(self):
        return f"{self.backend_url}/auth/github?state={self.state}&code_challenge={self.code_challenge}"

    def start_callback_server(self, port=8080):
        handler = CallbackHandler(self)
        server = HTTPServer(("localhost", port), handler)
        thread = Thread(target=server.handle_request)
        thread.daemon = True
        thread.start()
        return thread

    def initiate_login(self):
        self.generate_pkce()
        auth_url = self.get_auth_url()
        webbrowser.open(auth_url)
        self.start_callback_server()

    def exchange_code_for_tokens(self):
        if not self.auth_code:
            raise Exception("No authorization code received")

        response = requests.post(
            f"{self.backend_url}/auth/github/callback",
            params={
                "code": self.auth_code,
                "state": self.state,
                "code_verifier": self.code_verifier,
            },
        )

        if response.status_code != 200:
            raise Exception(f"Failed to exchange code: {response.status_code}")

        return response.json()


class CallbackHandler(BaseHTTPRequestHandler):
    def __init__(self, oauth_handler, *args, **kwargs):
        self.oauth_handler = oauth_handler
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/callback":
            query = parse_qs(parsed.query)
            code = query.get("code", [None])[0]
            state = query.get("state", [None])[0]

            if state == self.oauth_handler.state:
                self.oauth_handler.auth_code = code
                self.oauth_handler.callback_received = True
                message = b"<html><body><h1>Authentication successful! You can close this window.</h1></body></html>"
            else:
                message = b"<html><body><h1>Authentication failed: Invalid state. Please try again.</h1></body></html>"

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(message)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass
