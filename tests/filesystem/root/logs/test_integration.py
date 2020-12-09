from pathlib import Path
from zipfile import ZipFile

import pytest

from api_iso_antares.custom_types import SUB_JSON
from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.root.study import Study
from tests.filesystem.utils import extract_sta


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
def test_get_logs_it(
    project_path: Path, tmp_path: Path, url: str, exp: SUB_JSON
):
    pass
    # path = extract_sta(project_path, tmp_path)
    # study = Study(config=Config(path))


#
# # TODO assert study.get(url.split("/")) == exp
