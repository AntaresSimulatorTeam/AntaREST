from starlette.testclient import TestClient

from antarest import __version__


def test_apidoc(client: TestClient) -> None:
    # Local import to avoid breaking all tests if FastAPI changes its API
    from fastapi.openapi.utils import get_openapi

    routes = client.app.routes
    openapi = get_openapi(title="Antares Web", version=__version__, routes=routes)
    assert openapi
