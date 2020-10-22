from jsonschema import Draft7Validator

from api_iso_antares.custom_types import JSON
from api_iso_antares.jsonschema import JsonSchema


class JsmValidator:
    def __init__(self, jsm: JsonSchema) -> None:
        self.jsm = jsm
        self.validator: Draft7Validator
        self._init_validator()

    def _init_validator(self) -> None:
        self.validator = Draft7Validator(self.jsm.data)
        Draft7Validator.check_schema(self.jsm.data)

    def validate(self, jsondata: JSON) -> None:
        self.validator.validate(jsondata, self.jsm.data)
