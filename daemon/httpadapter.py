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
from .dictionary import CaseInsensitiveDict

ERRORS = CaseInsensitiveDict({
    "unauthorized": {
        "status": "401 Unauthorized",
        "content_type": "text/html; charset=utf-8",
        "headers": {},
        "body": (
            "<html><head><title>401</title></head>"
            "<body><h1>401 Unauthorized</h1>"
            "<p>Please <a href='/login.html'>login</a> first</p>"
            "</body></html>"
        ).encode("utf-8"),
    },
    "login_failed": {
        "status": "401 Unauthorized",
        "content_type": "text/html; charset=utf-8",
        "headers": {},
        "body": (
            "<html><head><title>Login Failed</title></head>"
            "<body><h1>401 Unauthorized</h1>"
            "<p>Invalid username or password</p>"
            "<p><a href='/login.html'>Try again</a></p>"
            "</body></html>"
        ).encode("utf-8"),
    },
    "not_found": {
        "status": "404 Not Found",
        "content_type": "text/html; charset=utf-8",
        "headers": {},
        "body": b"<h1>404 Not Found</h1>",
    },
    "server_error": {
        "status": "500 Internal Server Error",
        "content_type": "text/html; charset=utf-8",
        "headers": {},
        "body": b"<h1>500 Internal Server Error</h1>",
    },
    # JSON cho API/WeApRous
    "api_error": {
        "status": "500 Internal Server Error",
        "content_type": "application/json; charset=utf-8",
        "headers": {},
        "body": b'{"status":"error","message":"internal"}',
    },
})

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
            raw = self._read_from_socket(conn)

            # 2) Parse into Request object
            self._parse_into_request(req, raw, routes)

            # ----- Task 1A: /login (bypass cookie guard) -----
            if req.method == "POST" and req.path == "/login":
                return self._send(resp, self._handle_login(req, resp))

            # ----- Task 1B: Cookie guard for "/" and "/index.html" -----
            early = self._cookie_auth_guard(req)
            if early is not None:
                return self._send(resp, early)

            # ----- Task 2: WeApRous hook (priority) or Static file -----
            return self._send(resp, self._dispatch(req, resp))

        except Exception as e:
            # Fallback 500 using error catalog (with a small runtime hint inside HTML comment)
            e_tmpl = ERRORS["server_error"]
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

    def _read_from_socket(self, conn) -> str:
        """
        Minimal read: one recv() call. For larger bodies, extend to loop until Content-Length is satisfied.
        """
        return conn.recv(1024).decode("utf-8", "ignore")

    # -------------------- Parse --------------------

    def _parse_into_request(self, req, raw: str, routes):
        """
        Let Request.parse do the heavy-lifting; then ensure req.cookies and req.body exist.
        """
        req.prepare(raw, routes)
        # Ensure req.body is text-friendly for API handling (keep bytes in req.body; decode when needed)
        if not hasattr(req, "body") or req.body is None:
            req.body = b""

    # -------------------- Task 1: Cookie Session --------------------

    def _handle_login(self, req, resp):
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
            # Serve index.html via existing static pipeline (reuse build_response)
            req.path = "/index.html"
            raw = resp.build_response(req)  # returns full bytes (headers + body)
            # Extract body to re-compose with Set-Cookie
            body = raw.split(b"\r\n\r\n", 1)[1] if b"\r\n\r\n" in raw else raw
            headers = {
                "Content-Type": "text/html; charset=utf-8",
                "Set-Cookie": "auth=true; Path=/",
            }
            return ("200 OK", headers, body)

        # Wrong credentials -> 401 from catalog
        e = ERRORS["login_failed"]
        return (e["status"], {"Content-Type": e["content_type"], **e["headers"]}, e["body"])

    def _cookie_auth_guard(self, req):
        """
        Protect "/" and "/index.html" as per assignment: require Cookie 'auth=true'.
        Return a (status, headers, body) triple to short-circuit, or None to continue.
        """
        if req.path in ("/", "/index.html"):
            if req.cookies.get("auth") != "true":
                e = ERRORS["unauthorized"]
                return (e["status"], {"Content-Type": e["content_type"], **e["headers"]}, e["body"])
        return None

    # -------------------- Task 2: WeApRous & Static --------------------

    def _dispatch(self, req, resp):
        """
        Dispatch priority:
        1) WeApRous route hook if available
        2) Static file pipeline (default)
        """
        if req.hook:
            return self._handle_weaprous(req, resp)
        return self._handle_static(req, resp)

    def _handle_weaprous(self, req, resp):
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
        try:
            # Body as text for typical JSON APIs
            body_text = req.body.decode("utf-8", "ignore") if isinstance(req.body, (bytes, bytearray)) else (req.body or "")
            result = req.hook(headers=req.headers, body=body_text)

            # Normalize results
            if isinstance(result, tuple) and len(result) == 3:
                status, headers, body = result
                if isinstance(body, (dict, list)):
                    body = json.dumps(body).encode("utf-8")
                    headers = {"Content-Type": "application/json; charset=utf-8", **(headers or {})}
                elif isinstance(body, str):
                    body = body.encode("utf-8")
                headers = {"Access-Control-Allow-Origin": "*", **(headers or {})}
                return status, headers, body

            if result is None:
                payload = {"status": "success"}
                return ("200 OK",
                        {"Content-Type": "application/json; charset=utf-8",
                         "Access-Control-Allow-Origin": "*"},
                        json.dumps(payload).encode("utf-8"))

            if isinstance(result, (dict, list)):
                return ("200 OK",
                        {"Content-Type": "application/json; charset=utf-8",
                         "Access-Control-Allow-Origin": "*"},
                        json.dumps(result).encode("utf-8"))

            if isinstance(result, str):
                return ("200 OK",
                        {"Content-Type": "text/plain; charset=utf-8",
                         "Access-Control-Allow-Origin": "*"},
                        result.encode("utf-8"))

            # Fallback: stringify unknown types
            return ("200 OK",
                    {"Content-Type": "text/plain; charset=utf-8",
                     "Access-Control-Allow-Origin": "*"},
                    str(result).encode("utf-8"))

        except Exception as ex:
            # 500 JSON with catalog style
            msg = '{{"status":"error","message":"{}"}}'.format(str(ex)).encode("utf-8")
            return ("500 Internal Server Error",
                    {"Content-Type": "application/json; charset=utf-8"},
                    msg)

    def _handle_static(self, req, resp):
        """
        Default static pipeline: reuse existing Response.build_response(req),
        which already determines base dir and content type for files.
        """
        raw = resp.build_response(req)  # already full bytes (headers+body)
        return ("__RAW__", None, raw)

    # -------------------- Send --------------------

    def _send(self, resp, triple):
        """
        Send a (status, headers, body) triple to the client.
        If status is "__RAW__", send bytes as-is (already composed).
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
