from pathlib import Path

import pytest

from api_iso_antares.antares_io.reader import JsmReader
from api_iso_antares.antares_io.validator.jsonschema import JsmValidator
from api_iso_antares.custom_types import JSON


@pytest.mark.unit_test
def test_validate(
    path_ressources: Path,
    path_jsm_with_refs_outside: Path,
    lite_jsondata: JSON,
) -> None:

    jsm = JsmReader.read(path_jsm_with_refs_outside)
    validator = JsmValidator(jsm=jsm)

    try:
        validator.validate(lite_jsondata)
    except Exception as e:
        print(e)
        pytest.fail()
