from pathlib import Path

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.raw_file_node import RawFileNode


def test_get(tmp_path: Path) -> None:
    (tmp_path / "my-study/a/b").mkdir(parents=True)
    (tmp_path / "my-study/a/b/c").touch()
    config = StudyConfig(
        study_path=tmp_path / "my-study", areas=dict(), outputs=dict()
    )
    config = config.next_file("a").next_file("b").next_file("c")

    node = RawFileNode(config=config)
    assert node.get() == "file/my-study/a/b/c"


def test_validate(tmp_path: Path) -> None:
    file = tmp_path / "file"
    file.touch()

    node = RawFileNode(config=StudyConfig(study_path=file))
    assert node.validate(data=None) == []

    node = RawFileNode(config=StudyConfig(study_path=tmp_path / "nofile"))
    assert "not exist" in node.validate(data=None)[0]


def test_save(tmp_path: Path) -> None:
    (tmp_path / "studyA").mkdir()
    (tmp_path / "studyA/my-file").write_text("Hello, World")
    (tmp_path / "studyB").mkdir()

    config = StudyConfig(
        study_path=tmp_path / "studyB", areas=dict(), outputs=dict()
    ).next_file("my-file")
    node = RawFileNode(config=config)

    node.save("file/studyA/my-file")
    assert (tmp_path / "studyB/my-file").read_text() == "Hello, World"
