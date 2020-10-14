from pathlib import Path

import pytest

from api_iso_antares.antares_io.validator.jsonschema import Validator
from api_iso_antares.custom_types import JSON


@pytest.mark.unit_test
def test_validate(
    path_ressources: Path,
    jsonschema_with_refs_outside: JSON,
    lite_jsondata: Path,
) -> None:

    validator = Validator(
        root_resolver=path_ressources, jsm=jsonschema_with_refs_outside
    )

    try:
        validator.validate(lite_jsondata)
    except Exception as e:
        print(e)
        pytest.fail()
