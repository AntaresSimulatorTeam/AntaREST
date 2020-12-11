import shutil
from pathlib import Path

from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.raw_file_node import RawFileNode


def test_get(tmp_path: Path):
    (tmp_path / "my-study/a/b").mkdir(parents=True)
    (tmp_path / "my-study/a/b/c").touch()
    config = Config(
        study_path=tmp_path / "my-study", areas=dict(), outputs=dict()
    )
    config = config.next_file("a").next_file("b").next_file("c")

    node = RawFileNode(config=config)
    assert node.get() == "file/my-study/a/b/c"


def test_save(tmp_path: Path):
    (tmp_path / "studyA").mkdir()
    (tmp_path / "studyA/my-file").write_text("Hello, World")
    (tmp_path / "studyB").mkdir()

    config = Config(
        study_path=tmp_path / "studyB", areas=dict(), outputs=dict()
    ).next_file("my-file")
    node = RawFileNode(config=config)

    node.save("file/studyA/my-file")
    assert (tmp_path / "studyB/my-file").read_text() == "Hello, World"
