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

    # TODO: remove those two lines
    # yaml_swg = SwaggerEngine.json_to_yaml(swg_doc)
    # (project_path / "swagger.yaml").write_text(yaml_swg)

    SwaggerValidator.validate(swg_doc)
