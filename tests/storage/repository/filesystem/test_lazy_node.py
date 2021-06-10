from pathlib import Path
from typing import Optional, List

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.inode import V, S, G, TREE
from antarest.storage.repository.filesystem.lazy_node import LazyNode


class MockLazyNode(LazyNode[str, str, str]):
    def __init__(self, path: Optional[Path] = None) -> None:
        super().__init__(url_prefix="file")
        if path:
            self.config = StudyConfig(study_path=path)

    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return "Hello"

    def dump(self, data: str, url: Optional[List[str]] = None) -> None:
        self.config.path.write_text(data)

    def build(self, config: StudyConfig) -> TREE:
        pass  # not used

    def check_errors(
        self, data: str, url: Optional[List[str]] = None, raising: bool = False
    ) -> List[str]:
        pass  # not used


def test_get(tmp_path: Path):
    file = tmp_path / "lazy.txt"

    node = MockLazyNode(file)
    assert "lazy.txt" in node.get(expanded=True)

    assert "Hello" == node.get()


def test_save(tmp_path: Path):
    file = tmp_path / "lazy.txt"
    file.touch()

    src = tmp_path / "src.txt"
    src.write_text("Lazy")

    node = MockLazyNode(file)

    node.save(f"file://{src.absolute()}")
    assert file.read_text() == "Lazy"

    node.save("Not Lazy")
    assert file.read_text() == "Not Lazy"
