from pathlib import Path
from zipfile import ZipFile

import pytest

from api_iso_antares.custom_types import SUB_JSON
from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.root.study import Study
from tests.domain.study.utils import extract_sta


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, exp",
    [
        ("input/areas/de/ui/ui/x", 1),
        (
            "input/areas/de/optimization/filtering/filter-synthesis",
            "daily, monthly",
        ),
        ("input/areas/list", "file/STA-mini/input/areas/list.txt"),
    ],
)
def test_get_input_it(
    project_path: Path, tmp_path: Path, url: str, exp: SUB_JSON
) -> None:
    path = extract_sta(project_path, tmp_path)
    study = Study(config=Config(path))

    assert study.get(url.split("/")) == exp


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, exp",
    [
        ("input/areas/de/ui/ui/x", 42),
        (
            "input/areas/de/optimization/filtering/filter-synthesis",
            "Hello, World",
        ),
    ],
)
def test_save_settings_it(
    project_path: Path, tmp_path: Path, url: str, exp: SUB_JSON
) -> None:
    path = extract_sta(project_path, tmp_path)
    study = Study(config=Config(path))

    study.save(exp, url.split("/"))
    assert study.get(url.split("/")) == exp
