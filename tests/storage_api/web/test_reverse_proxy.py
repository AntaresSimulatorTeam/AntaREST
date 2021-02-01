from antarest.storage_api.web import ReverseProxyMiddleware

import pytest

from unittest.mock import create_autospec


def wsgi_app_function(environ, start_response):
    pass


@pytest.mark.unit_test
def test_wrapper():
    wsgi_app = create_autospec(wsgi_app_function)
    proxyied_app = ReverseProxyMiddleware(wsgi_app)
    environ = {}
    start_response = None
    proxyied_app(environ, start_response)
    wsgi_app.assert_called_with({}, start_response)

    environ = {
        "HTTP_X_SCRIPT_NAME": "/api",
        "HTTP_X_FORWARDED_HOST": "foo:5000",
        "HTTP_X_SCHEME": "https",
    }
    start_response = None
    proxyied_app(environ, start_response)
    wsgi_app.assert_called_with(
        {
            "HTTP_X_SCRIPT_NAME": "/api",
            "SCRIPT_NAME": "/api",
            "HTTP_X_FORWARDED_HOST": "foo:5000",
            "HTTP_HOST": "foo:5000",
            "HTTP_X_SCHEME": "https",
            "wsgi.url_scheme": "https",
        },
        start_response,
    )
