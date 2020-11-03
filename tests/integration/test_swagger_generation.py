from pathlib import Path

import pytest

from api_iso_antares.antares_io.reader import JsmReader
from api_iso_antares.antares_io.validator import SwaggerValidator
from api_iso_antares.engine.swagger.engine import SwaggerEngine


@pytest.mark.integration_test
def test_generation_swagger_documentation(
    project_path: Path, path_jsm: Path
) -> None:
    jsm = JsmReader.read(path_jsm)
    swg_doc = SwaggerEngine.parse(jsm)

    SwaggerValidator.validate(swg_doc)
