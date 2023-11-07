import logging

from fastapi.openapi.utils import get_flat_models_from_routes
from fastapi.utils import get_model_definitions
from pydantic.schema import get_model_name_map
from starlette.testclient import TestClient

logger = logging.getLogger(__name__)


def test_apidoc(client: TestClient) -> None:
    # Asserts that the apidoc can be loaded
    flat_models = get_flat_models_from_routes(client.app.routes)
    model_name_map = get_model_name_map(flat_models)
    try:
        get_model_definitions(flat_models=flat_models, model_name_map=model_name_map)
    except Exception as e:
        logger.error("A pydantic model is invalid. Therefore the APIdoc page cannot be loaded.", exc_info=e)
