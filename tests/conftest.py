import sys
from pathlib import Path

import pytest

project_dir: Path = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))


@pytest.fixture
def project_path() -> Path:
    return project_dir
