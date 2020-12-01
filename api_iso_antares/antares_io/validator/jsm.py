from typing import Optional

from jsonschema import Draft7Validator

from api_iso_antares.custom_types import JSON
from api_iso_antares.jsm import JsonSchema


class JsmValidator:
    def __init__(self, jsm: JsonSchema) -> None:
        self.jsm = jsm
        self._validator: Draft7Validator
        self._init_validator()

    def _init_validator(self) -> None:
        self._validator = Draft7Validator(self.jsm.data)
        Draft7Validator.check_schema(self.jsm.data)

    def validate(
        self, jsondata: JSON, sub_jsm: Optional[JsonSchema] = None
    ) -> None:
        jsm = sub_jsm or self.jsm
        self._validator.validate(jsondata, jsm.data)
