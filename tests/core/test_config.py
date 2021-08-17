import os
from pathlib import Path

import pytest

from antarest.core.config import Config


@pytest.mark.unit_test
def test_get_yaml(project_path: Path):
    config = Config.from_yaml_file(
        file=project_path / "resources/application.yaml"
    )

    assert config.security.admin_pwd == "admin"
    assert config.storage.workspaces["default"].path == Path(
        "examples/internal_studies/"
    )
    assert not config.logging.json
    assert config.logging.level == "INFO"
