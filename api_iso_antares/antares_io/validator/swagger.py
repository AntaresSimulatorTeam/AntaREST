import json
import urllib.request
from typing import cast

from jsonschema import Draft7Validator

from api_iso_antares.custom_types import JSON

JSONSCHEMA_OPENAPI_VALIDATOR_URL = "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/schemas/v3.0/schema.json"


class SwaggerValidator:
    @staticmethod
    def _load_url(url: str) -> bytes:
        with urllib.request.urlopen(url) as response:
            data = response.read()
        return cast(bytes, data)

    @staticmethod
    def _get_jsondata_from_url(url: str) -> JSON:
        data = SwaggerValidator._load_url(url)
        return cast(JSON, json.loads(data))

    @staticmethod
    def _get_jsonschema_swagger() -> JSON:
        json_data = SwaggerValidator._get_jsondata_from_url(
            JSONSCHEMA_OPENAPI_VALIDATOR_URL
        )
        return json_data

    @staticmethod
    def _get_validator_swagger() -> Draft7Validator:
        jsm_swagger = SwaggerValidator._get_jsonschema_swagger()
        return Draft7Validator(jsm_swagger)

    @staticmethod
    def validate(data: JSON) -> None:
        jsm_validator = SwaggerValidator._get_validator_swagger()
        jsm_validator.validate(data)
