from pathlib import Path
from typing import Optional, List
from unittest.mock import Mock

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode


class MockLazyNode(LazyNode[str, str, str]):
    def normalize(self) -> None:
        pass  # no external store in this node

    def denormalize(self) -> None:
        pass  # no external store in this node

    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig
    ) -> None:
        super().__init__(
            config=config,
            context=context,
        )

    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = False,
    ) -> str:
        return "Mock Matrix Content"

    def dump(self, data: str, url: Optional[List[str]] = None) -> None:
        self.config.path.write_text(data)

    def build(self, config: FileStudyTreeConfig) -> TREE:
        pass  # not used

    def check_errors(
        self, data: str, url: Optional[List[str]] = None, raising: bool = False
    ) -> List[str]:
        pass  # not used


def test_get_no_expanded_txt(tmp_path: Path):
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()
    file.touch()

    config = FileStudyTreeConfig(
        study_path=file, path=file, version=-1, study_id="my-study"
    )

    node = MockLazyNode(
        context=ContextServer(matrix=Mock(), resolver=Mock()),
        config=config,
    )
    assert "Mock Matrix Content" == node.get(expanded=False)


def test_get_no_expanded_link(tmp_path: Path):
    uri = "matrix://my-link"

    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()
    (file.parent / "lazy.txt.link").write_text(uri)

    config = FileStudyTreeConfig(
        study_path=file, path=file, version=-1, study_id="my-study"
    )

    resolver = Mock()
    resolver.resolve.return_value = "Mock Matrix Content"

    node = MockLazyNode(
        context=ContextServer(matrix=Mock(), resolver=resolver),
        config=config,
    )
    assert "Mock Matrix Content" == node.get(expanded=False)
    resolver.resolve.assert_called_once_with(uri)


def test_get_expanded_txt(tmp_path: Path):
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()
    file.touch()

    config = FileStudyTreeConfig(
        study_path=file, path=file, version=-1, study_id="my-study"
    )

    node = MockLazyNode(
        context=ContextServer(matrix=Mock(), resolver=Mock()),
        config=config,
    )
    assert "file://lazy.txt" == node.get(expanded=True)


def test_get_expanded_link(tmp_path: Path):
    uri = "matrix://my-link"

    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()
    (file.parent / "lazy.txt.link").write_text(uri)

    config = FileStudyTreeConfig(
        study_path=file, path=file, version=-1, study_id="my-study"
    )

    node = MockLazyNode(
        context=ContextServer(matrix=Mock(), resolver=Mock()),
        config=config,
    )
    assert uri == node.get(expanded=True)


def test_save_uri(tmp_path: Path):
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()
    file.touch()

    resolver = Mock()
    resolver.resolve.return_value = "Lazy"

    config = FileStudyTreeConfig(
        study_path=file, path=file, version=-1, study_id=""
    )
    context = ContextServer(matrix=Mock(), resolver=resolver)
    node = MockLazyNode(context=context, config=config)

    uri = f"matrix://id"
    node.save(uri)
    assert (file.parent / f"{file.name}.link").read_text() == uri
    assert not file.exists()
    resolver.resolve.assert_called_once_with(uri)


def test_save_txt(tmp_path: Path):
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()

    link = file.parent / f"{file.name}.link"
    link.touch()

    resolver = Mock()
    resolver.resolve.return_value = None

    config = FileStudyTreeConfig(
        study_path=file, path=file, version=-1, study_id=""
    )
    context = ContextServer(matrix=Mock(), resolver=resolver)
    node = MockLazyNode(context=context, config=config)

    content = "Mock File Content"
    node.save(content)
    assert file.read_text() == content
    assert not link.exists()
    resolver.resolve.assert_called_once_with(content)
