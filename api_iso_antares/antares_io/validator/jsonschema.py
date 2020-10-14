import os
from pathlib import Path

from jsonschema import Draft7Validator, RefResolver

from api_iso_antares.custom_types import JSON


class Validator:
    def __init__(self, root_resolver: Path, jsm: JSON) -> None:

        self.root_resolver = root_resolver
        self.jsm = jsm
        self.validator: Draft7Validator
        self._init_validator()

    def _init_validator(self) -> None:

        resolver = RefResolver(
            base_uri=f"file:{self.root_resolver}" + os.sep,
            referrer=self.jsm,
        )

        self.validator = Draft7Validator(self.jsm, resolver=resolver)
        Draft7Validator.check_schema(self.jsm)

    def validate(self, jsondata: JSON) -> None:
        self.validator.validate(jsondata, self.jsm)
