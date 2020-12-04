from pathlib import Path
from zipfile import ZipFile

import pytest

from api_iso_antares.custom_types import SUB_JSON
from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.root.study import Study


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, exp",
    [
        ("desktop/.shellclassinfo/iconindex", 0),
        ("study/antares/author", "Andrea SGATTONI"),
        (
            "settings/resources/study",
            "file/STA-mini/settings/resources/study.icon",
        ),
        (
            "settings/comments",
            "file/STA-mini/settings/comments.txt",
        ),
        ("settings/generaldata/general/horizon", 2030),
        ("settings/scenariobuilder/Default Ruleset/l,fr,0", 1),
    ],
)
def test_get_settings_it(
    project_path: Path, tmp_path: Path, url: str, exp: SUB_JSON
):
    path_studies = tmp_path / "studies"
    with ZipFile(project_path / "examples/studies/STA-mini.zip") as zip_output:
        zip_output.extractall(path=path_studies)

    study = Study(config=Config(path_studies / "STA-mini"))

    assert study.get(url.split("/")) == exp


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, exp",
    [
        ("desktop/.shellclassinfo/iconindex", 10),
        ("study/antares/author", "John"),
        ("settings/generaldata/general/horizon", 1984),
        ("settings/scenariobuilder/Default Ruleset/l,fr,0", 42),
    ],
)
def test_get_settings_it(
    project_path: Path, tmp_path: Path, url: str, exp: SUB_JSON
):
    path_studies = tmp_path / "studies"
    with ZipFile(project_path / "examples/studies/STA-mini.zip") as zip_output:
        zip_output.extractall(path=path_studies)

    study = Study(config=Config(path_studies / "STA-mini"))

    study.save(exp, url.split("/"))
    assert study.get(url.split("/")) == exp
