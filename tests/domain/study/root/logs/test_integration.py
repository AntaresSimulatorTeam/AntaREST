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
        (
            "logs/solver-20201014-142220",
            "file/STA-mini/logs/solver-20201014-142220.log",
        ),
    ],
)
def test_get_layers_it(
    project_path: Path, tmp_path: Path, url: str, exp: SUB_JSON
):
    path = extract_sta(project_path, tmp_path)
    study = Study(config=Config(path))

    assert study.get(url.split("/")) == exp
