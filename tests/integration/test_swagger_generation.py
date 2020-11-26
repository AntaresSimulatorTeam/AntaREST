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
    # path_swagger = project_path / "swagger.json"
    # json.dump(swg_doc, path_swagger.open("w"), indent=2)

    SwaggerValidator.validate(swg_doc)

    urls = swg_doc.get("paths").keys()
    url_studies = "/studies"
    url_study = "/studies/{uuid}"
    url_create_study = "/studies/{uuid}"
    url_copy_study = "/studies/{uuid}/copy"

    long_url = "/studies/{uuid}/output/{simulation}/about-the-study/parameters/general"

    assert url_studies in urls
    assert url_study in urls
    assert url_create_study in urls
    assert url_copy_study in urls
    assert long_url not in urls

    paths = swg_doc.get("paths")
    study_path = paths.get("/studies/{uuid}")

    assert "delete" in study_path

    studies_path = paths.get("/studies")
    assert "post" in studies_path

    get_file_path = paths.get("/file/{path}")
    assert "get" in get_file_path
    assert "post" in get_file_path
