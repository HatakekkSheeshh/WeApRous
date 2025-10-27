#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.httpadapter
~~~~~~~~~~~~~~~~~

This module provides a http adapter object to manage and persist 
http settings (headers, bodies). The adapter supports both
raw URL paths and RESTful route definitions, and integrates with
Request and Response objects to handle client-server communication.
"""

from .request import Request
from .response import Response
# from .dictionary import CaseInsensitiveDict
from .resp_template import RESP_TEMPLATES
from .utils import get_auth_from_url

class HttpAdapter:
    """
    A mutable :class:`HTTP adapter <HTTP adapter>` for managing client connections
    and routing requests.

    The `HttpAdapter` class encapsulates the logic for receiving HTTP requests,
    dispatching them to appropriate route handlers, and constructing responses.
    It supports RESTful routing via hooks and integrates with :class:`Request <Request>` 
    and :class:`Response <Response>` objects for full request lifecycle management.

    Attributes:
        ip (str): IP address of the client.
        port (int): Port number of the client.
        conn (socket): Active socket connection.
        connaddr (tuple): Address of the connected client.
        routes (dict): Mapping of route paths to handler functions.
        request (Request): Request object for parsing incoming data.
        response (Response): Response object for building and sending replies.
    """

    __attrs__ = [
        "ip",
        "port",
        "conn",
        "connaddr",
        "routes",
        "request",
        "response",
    ]

    def __init__(self, ip, port, conn, connaddr, routes):
        """
        Initialize a new HttpAdapter instance.

        :param ip (str): IP address of the client.
        :param port (int): Port number of the client.
        :param conn (socket): Active socket connection.
        :param connaddr (tuple): Address of the connected client.
        :param routes (dict): Mapping of route paths to handler functions.
        """

        #: IP address.
        self.ip = ip
        #: Port.
        self.port = port
        #: Connection
        self.conn = conn
        #: Conndection address
        self.connaddr = connaddr
        #: Routes
        self.routes = routes
        #: Request
        self.request = Request()
        #: Response
        self.response = Response()

    def handle_client(self, conn, addr, routes):
        """
        Handle an incoming client connection.

        This method reads the request from the socket, prepares the request object,
        invokes the appropriate route handler if available, builds the response,
        and sends it back to the client.

        :param conn (socket): The client socket connection.
        :param addr (tuple): The client's address.
        :param routes (dict): The route mapping for dispatching requests.
        """

        # Connection handler.
        self.conn = conn        
        # Connection address.
        self.connaddr = addr
        # Request handler
        req = self.request
        # Response handler
        resp = self.response

        try:
            # 1) Read from socket (minimal read; can be extended to read full Content-Length)
            raw = self.read_from_socket(conn)

            # 2) Parse into Request object
            self.parse_into_request(req, raw, routes)
                
            # --------------------------- Task 1 ---------------------------

            # ----- Task 1A: /login (bypass cookie guard) ----
            if len(routes) <= 0:
                if req.method == "POST" and req.path == "/login":
                    return self.send(resp, self.handle_login(req, resp))

            # ----- Task 1B: Cookie guard for "/" and "/index.html" -----
            early = self.cookie_auth_guard(req)
            if early is not None:
                return self.send(resp, early)

            # ----- Task 2: WeApRous hook (priority) or Static file -----
            return self.send(resp, self.dispatch(req, resp))

        except Exception as e:
            # Fallback 500 using error catalog (with a small runtime hint inside HTML comment)
            e_tmpl = RESP_TEMPLATES["server_error"]
            body = e_tmpl["body"] + f"\n<!-- {str(e)} -->".encode("utf-8")
            return self.conn.sendall(resp.compose(
                status=e_tmpl["status"],
                headers={"Content-Type": e_tmpl["content_type"], **e_tmpl["headers"]},
                body=body
            ))
        finally:
            try:
                conn.close()
            except:
                pass


    # -------------------- I/O --------------------

    def read_from_socket(self, conn) -> str:
        """
        Minimal read: one recv() call. For larger bodies, extend to loop until Content-Length is satisfied.
        """
        return conn.recv(1024).decode("utf-8", "ignore")

    # -------------------- Parse --------------------

    def parse_into_request(self, req, raw: str, routes):
        """
        routes:
            weaprous routes: {"/login": login}
            static routes: {}
        """
        req.prepare(raw, routes)
        # Ensure req.body is text-friendly for API handling (keep bytes in req.body; decode when needed)
        if not hasattr(req, "body") or req.body is None:
            req.body = b""

    # -------------------- Task 1: Cookie Session --------------------

    def handle_login(self, req, resp):
        """
        POST /login as per assignment:
        - Accept simple form urlencoded 'username=...&password=...'
        - If admin/password -> Set-Cookie: auth=true; serve index.html
        - Else -> 401 using catalog
        """
        # Parse simple form body
        raw_body = req.body.decode("utf-8", "ignore") if isinstance(req.body, (bytes, bytearray)) else (req.body or "")
        creds = {}
        for pair in raw_body.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                creds[k] = v

        if creds.get("username") == "admin" and creds.get("password") == "password":
            req.path = "/index.html"
            raw = resp.build_response(req) 
            body = raw.split(b"\r\n\r\n", 1)[1] if b"\r\n\r\n" in raw else raw
            headers = {
                "Content-Type": "text/html; charset=utf-8",
                "Set-Cookie": "auth=true; Path=/",
            }
            return ("200 OK", headers, body)

        # Wrong credentials -> 401 from catalog
        e = RESP_TEMPLATES["login_failed"]
        return (e["status"], {"Content-Type": e["content_type"], **e["headers"]}, e["body"])

    def cookie_auth_guard(self, req):
        """
        Protect "/" and "/index.html" as per assignment: require Cookie 'auth=true'.
        Return a (status, headers, body) triple to short-circuit, or None to continue.
        """
        if req.path in ("/", "/index.html"):
            if req.cookies.get("auth") != "true":
                e = RESP_TEMPLATES["unauthorized"]
                return (e["status"], {"Content-Type": e["content_type"], **e["headers"]}, e["body"])
        if req.path == "/":
            req.path = "/index.html"
        return None

    # -------------------- Task 2: WeApRous & Static --------------------
    def handle_weaprous(self, req, resp):
        """
        Execute a route hook (callable) injected via routes mapping in Request.prepare().
        Result normalization:
        - tuple(status, headers, body) returned as-is (body may be bytes/str/dict/list)
        - dict/list -> JSON
        - str -> text/plain
        - None -> {"status":"success"}
        Errors -> 500 JSON
        """
        import json

        def to_bytes(body, current_ct=None):
            if isinstance(body, (bytes, bytearray)):
                return bytes(body), current_ct
            if body is None:
                return b'{"status":"success"}', "application/json; charset=utf-8"
            if isinstance(body, (dict, list)):
                return json.dumps(body).encode("utf-8"), "application/json; charset=utf-8"
            if isinstance(body, str):
                return body.encode("utf-8"), current_ct or "text/plain; charset=utf-8"
            return str(body).encode("utf-8"), current_ct or "text/plain; charset=utf-8"

        try:
            body_text = (
                req.body.decode("utf-8", "ignore")
                if isinstance(req.body, (bytes, bytearray))
                else (req.body or "")
            )

            result = req.hook(headers=req.headers, body=body_text)

            if isinstance(result, tuple) and len(result) == 3:
                status, headers, payload = result

                headers = dict(headers or {})
                payload_bytes, ct = to_bytes(payload, headers.get("Content-Type"))
                headers.setdefault("Content-Type", ct)
                headers.setdefault("Access-Control-Allow-Origin", "*")
                return status, headers, payload_bytes

            # case 2: hook return dict/list/str/None
            payload_bytes, ct = to_bytes(result)
            headers = {
                "Content-Type": ct,
                "Access-Control-Allow-Origin": "*",
            }
            return "200 OK", headers, payload_bytes

        except Exception as ex:
            err = {"status": "error", "error": str(ex)}
            return (
                "500 Internal Server Error",
                {
                    "Content-Type": "application/json; charset=utf-8",
                    "Access-Control-Allow-Origin": "*",
                },
                json.dumps(err).encode("utf-8"),
            )

    # -------------------- Send --------------------
    def dispatch(self, req, resp):
        """
        Dispatch priority:
        1) WeApRous route hook if available
        2) Static file pipeline (default)
        """
        if req.hook:
            return self.handle_weaprous(req, resp)
        return self.handle_static(req, resp)

    def handle_static(self, req, resp):
        """
        Default static pipeline: reuse existing Response.build_response(req),
        which already determines base dir and content type for files.
        """
        raw = resp.build_response(req)  
        return ("__RAW__", None, raw)

    def send(self, resp, triple):
        """
        Send a (status, headers, body) triple to the client.
        """
        status, headers, body = triple
        if status == "__RAW__":
            return self.conn.sendall(body)
        return self.conn.sendall(resp.compose(status=status, headers=headers, body=body))

    # -------------------- misculary function --------------------
    def extract_cookies(self, req: Request, resp: Response):
        """
        Build cookies from the :class:`Request <Request>` headers.

        :param req:(Request) The :class:`Request <Request>` object.
        :param resp: (Response) The res:class:`Response <Response>` object.
        :rtype: cookies - A dictionary of cookie key-value pairs.
        """
        
        cookies = {}
        headers = req.headers
        for header in headers:
            if header.startswith("Cookie:"):
                cookie_str = header.split(":", 1)[1].strip()
                for pair in cookie_str.split(";"):
                    key, value = pair.strip().split("=")
                    cookies[key] = value
        return cookies

    def build_response(self, req, resp):
        """Builds a :class:`Response <Response>` object 

        :param req: The :class:`Request <Request>` used to generate the response.
        :param resp: The  response object.
        :rtype: Response
        """
        """
        response = Response()

        # Set encoding.
        response.encoding = get_encoding_from_headers(response.headers)
        response.raw = resp
        response.reason = response.raw.reason

        if isinstance(req.url, bytes):
            response.url = req.url.decode("utf-8")
        else:
            response.url = req.url

        # Add new cookies from the server.
        response.cookies = extract_cookies(req)

        # Give the Response some context.
        response.request = req
        response.connection = self
        """
        return self.response.build_response(req)   

    # def get_connection(self, url, proxies=None):
        # """Returns a url connection for the given URL. 

        # :param url: The URL to connect to.
        # :param proxies: (optional) A Requests-style dictionary of proxies used on this request.
        # :rtype: int
        # """

        # proxy = select_proxy(url, proxies)

        # if proxy:
            # proxy = prepend_scheme_if_needed(proxy, "http")
            # proxy_url = parse_url(proxy)
            # if not proxy_url.host:
                # raise InvalidProxyURL(
                    # "Please check proxy URL. It is malformed "
                    # "and could be missing the host."
                # )
            # proxy_manager = self.proxy_manager_for(proxy)
            # conn = proxy_manager.connection_from_url(url)
        # else:
            # # Only scheme should be lower case
            # parsed = urlparse(url)
            # url = parsed.geturl()
            # conn = self.poolmanager.connection_from_url(url)

        # return conn


    def add_headers(self, request):
        """
        Add headers to the request.

        This method is intended to be overridden by subclasses to inject
        custom headers. It does nothing by default.

        
        :param request: :class:`Request <Request>` to add headers to.
        """
        pass


    def build_proxy_headers(self, proxy):
        """Returns a dictionary of the headers to add to any request sent
        through a proxy. 

        :class:`HttpAdapter <HttpAdapter>`.

        :param proxy: The url of the proxy being used for this request.
        :rtype: dict
        """
        headers = {}
        #
        # TODO: build your authentication here
        #       username, password =...
        # we provide dummy auth here
        #
        username, password = ("user1", "password")

        if username:
            headers["Proxy-Authorization"] = (username, password)

        return headers
