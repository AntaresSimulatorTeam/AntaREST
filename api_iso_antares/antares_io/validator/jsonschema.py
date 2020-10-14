from jsonschema import Draft7Validator

from api_iso_antares.custom_types import JSON


class Validator:
    def __init__(self, jsm: JSON) -> None:
        self.jsm = jsm
        self.validator: Draft7Validator
        self._init_validator()

    def _init_validator(self) -> None:
        self.validator = Draft7Validator(self.jsm)
        Draft7Validator.check_schema(self.jsm)

    def validate(self, jsondata: JSON) -> None:
        self.validator.validate(jsondata, self.jsm)
