class ReverseProxyMiddleware:
    """
    Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.
    In nginx:
    location /prefix {
        proxy_pass http://192.168.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Script-Name /prefix;
        }
    :param app: the WSGI application
    """

    def __init__(self, wsgi_app):  # type: ignore
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):  # type: ignore
        script_name = environ.get("HTTP_X_SCRIPT_NAME", "")
        if script_name:
            environ["SCRIPT_NAME"] = script_name
            path_info = environ.get("PATH_INFO", "")
            if path_info and path_info.startswith(script_name):
                environ["PATH_INFO"] = path_info[len(script_name) :]

        host = environ.get("HTTP_X_FORWARDED_HOST", "")

        if host:
            environ["HTTP_HOST"] = host

        scheme = environ.get("HTTP_X_SCHEME", "")

        if scheme:
            environ["wsgi.url_scheme"] = scheme

        return self.wsgi_app(environ, start_response)
