from pathlib import Path

from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.raw_file_node import RawFileNode


def test_get(project_path: Path):
    config = Config(study_path=project_path / "my-study")
    config = config.next_file("a").next_file("b").next_file("c")

    node = RawFileNode(config=config)
    assert node.get([]) == "file/my-study/a/b/c"
