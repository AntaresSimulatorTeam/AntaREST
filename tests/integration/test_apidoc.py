from fastapi.openapi.utils import get_flat_models_from_routes
from fastapi.utils import get_model_definitions
from pydantic.schema import get_model_name_map
from starlette.testclient import TestClient


def test_apidoc(client: TestClient) -> None:
    # Asserts that the apidoc can be loaded
    flat_models = get_flat_models_from_routes(client.app.routes)
    model_name_map = get_model_name_map(flat_models)
    get_model_definitions(flat_models=flat_models, model_name_map=model_name_map)
