from pathlib import Path
from typing import List, Optional
from unittest.mock import Mock

import pytest

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode


class MockLazyNode(LazyNode[str, str, str]):
    def normalize(self) -> None:
        pass  # no external store in this node

    def denormalize(self) -> None:
        pass  # no external store in this node

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig) -> None:
        super().__init__(
            config=config,
            context=context,
        )

    def load(self, url: Optional[List[str]] = None, depth: int = -1, expanded: bool = False, format: str = "") -> str:
        return "Mock Matrix Content"

    def dump(self, data: str, url: Optional[List[str]] = None) -> None:
        self.config.path.write_text(data)

    def check_errors(self, data: str, url: Optional[List[str]] = None, raising: bool = False) -> List[str]:
        pass  # not used


def test_get_no_expanded_txt(tmp_path: Path):
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()
    file.touch()

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="my-study")

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

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="my-study")

    resolver = Mock()
    resolver.resolve.return_value = "Mock Matrix Content"

    node = MockLazyNode(
        context=ContextServer(matrix=Mock(), resolver=resolver),
        config=config,
    )
    assert "Mock Matrix Content" == node.get(expanded=False)
    resolver.resolve.assert_called_once_with(uri, None)


def test_get_expanded_txt(tmp_path: Path):
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()
    file.touch()

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="my-study")

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

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="my-study")

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

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="")
    context = ContextServer(matrix=Mock(), resolver=resolver)
    node = MockLazyNode(context=context, config=config)

    uri = "matrix://id"
    node.save(uri)
    assert (file.parent / f"{file.name}.link").read_text() == uri
    assert not file.exists()
    resolver.resolve.assert_called_once_with(uri, format="json")


def test_save_txt(tmp_path: Path):
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()

    link = file.parent / f"{file.name}.link"
    link.touch()

    resolver = Mock()
    resolver.resolve.return_value = None

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="")
    context = ContextServer(matrix=Mock(), resolver=resolver)
    node = MockLazyNode(context=context, config=config)

    content = "Mock File Content"
    node.save(content)
    assert file.read_text() == content
    assert not link.exists()
    resolver.resolve.assert_called_once_with(content, format="json")


@pytest.mark.parametrize("target_is_link", [True, False])
def test_rename_file(tmp_path: Path, target_is_link: bool):
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()

    link = file.parent / f"{file.name}.link"
    link.write_text("Link: Mock File Content")

    resolver = Mock()
    resolver.resolve.return_value = None

    resolver2 = Mock()
    resolver2.resolve.return_value = None

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="")
    context = ContextServer(matrix=Mock(), resolver=resolver)
    node = MockLazyNode(context=context, config=config)

    renaming_file = file.parent / "lazy_rename.txt"
    renaming_link = file.parent / f"{renaming_file.name}.link"
    config2 = FileStudyTreeConfig(study_path=renaming_file, path=renaming_file, version=-1, study_id="")
    context2 = ContextServer(matrix=Mock(), resolver=resolver2)
    target = MockLazyNode(context=context2, config=config2)

    if target_is_link:
        assert not renaming_link.exists()
        assert link.exists()
        assert not file.exists()
        assert not renaming_file.exists()

        node.rename_file(target)

        assert not link.exists()
        assert renaming_link.exists()
        assert not file.exists()
        assert not renaming_file.exists()
        assert renaming_link.read_text() == "Link: Mock File Content"

    else:
        content = "No Link: Mock File Content"
        node.save(content)
        assert file.read_text() == content
        assert not link.exists()
        assert not renaming_file.exists()
        resolver.resolve.assert_called_once_with(content, format="json")

        node.rename_file(target)

        assert not link.exists()
        assert not file.exists()
        assert renaming_file.exists()
        assert not renaming_link.exists()
        assert renaming_file.read_text() == "No Link: Mock File Content"


@pytest.mark.parametrize("target_is_link", [True, False])
def test_copy_file(tmp_path: Path, target_is_link: bool):
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()

    link = file.parent / f"{file.name}.link"
    link.write_text("Link: Mock File Content")

    resolver = Mock()
    resolver.resolve.return_value = None

    resolver2 = Mock()
    resolver2.resolve.return_value = None

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="")
    context = ContextServer(matrix=Mock(), resolver=resolver)
    node = MockLazyNode(context=context, config=config)

    copied_file = file.parent / "lazy_copy.txt"
    copied_link = file.parent / f"{copied_file.name}.link"
    config2 = FileStudyTreeConfig(study_path=copied_file, path=copied_file, version=-1, study_id="")
    context2 = ContextServer(matrix=Mock(), resolver=resolver2)
    target = MockLazyNode(context=context2, config=config2)

    if target_is_link:
        assert not copied_link.exists()
        assert link.exists()
        assert not file.exists()
        assert not copied_file.exists()

        node.copy_file(target)

        assert link.exists()
        assert copied_link.exists()
        assert not file.exists()
        assert not copied_file.exists()
        assert copied_link.read_text() == "Link: Mock File Content"

    else:
        content = "No Link: Mock File Content"
        node.save(content)
        assert file.read_text() == content
        assert not link.exists()
        assert not copied_file.exists()
        resolver.resolve.assert_called_once_with(content, format="json")

        node.copy_file(target)

        assert not link.exists()
        assert file.exists()
        assert copied_file.exists()
        assert not copied_link.exists()
        assert copied_file.read_text() == "No Link: Mock File Content"
