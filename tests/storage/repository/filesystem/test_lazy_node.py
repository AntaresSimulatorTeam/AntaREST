import itertools
import shutil
from pathlib import Path
from typing import List, Optional
from unittest.mock import Mock

import pytest

from antarest.core.exceptions import ChildNotFoundError
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
    resolver.resolve.assert_called_once_with(uri, True)


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
    resolver.resolve.assert_called_once_with(uri)


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
    resolver.resolve.assert_called_once_with(content)


class TestCopyAndRenameFile:
    node: MockLazyNode
    fake_node: MockLazyNode
    target: List[str]
    file: Path
    link: Path
    modified_file: Path
    modified_link: Path
    resolver: Mock

    def _set_up(self, tmp_path: Path, target_is_link: bool) -> None:
        self.file = tmp_path / "my-study" / "lazy.txt"
        self.file.parent.mkdir()

        self.link = self.file.parent / f"{self.file.name}.link"
        self.link.write_text("Link: Mock File Content")

        self.resolver = Mock()
        self.resolver.resolve.return_value = None

        config = FileStudyTreeConfig(study_path=self.file.parent, path=self.file, version=-1, study_id="")
        context = ContextServer(matrix=Mock(), resolver=self.resolver)
        self.node = MockLazyNode(context=context, config=config)

        self.modified_file = self.file.parent / "lazy_modified.txt"
        self.modified_link = self.file.parent / f"{self.modified_file.name}.link"
        config2 = FileStudyTreeConfig(study_path=self.file.parent, path=self.modified_file, version=-1, study_id="")
        self.fake_node = MockLazyNode(context=Mock(), config=config2)
        target_path = self.modified_link if target_is_link else self.modified_file
        self.target = list(target_path.relative_to(config.study_path).parts)

    def _checks_behavior(self, rename: bool, target_is_link: bool):
        # Asserts `_infer_path` fails if there's no file
        with pytest.raises(ChildNotFoundError):
            self.fake_node._infer_path()

        # Checks `copy_file`, `rename_file` and `get_suffixes` methods
        if target_is_link:
            assert not self.modified_link.exists()
            assert self.link.exists()
            assert not self.file.exists()
            assert not self.modified_file.exists()
            assert self.node.get_suffixes() == [".txt", ".link"]

            self.node.rename_file(self.target) if rename else self.node.copy_file(self.target)

            assert not self.link.exists() if rename else self.link.exists()
            assert self.modified_link.exists()
            assert not self.file.exists()
            assert not self.modified_file.exists()
            assert self.modified_link.read_text() == "Link: Mock File Content"

        else:
            content = "No Link: Mock File Content"
            self.node.save(content)
            assert self.file.read_text() == content
            assert not self.link.exists()
            assert not self.modified_file.exists()
            self.resolver.resolve.assert_called_once_with(content)
            assert self.node.get_suffixes() == [".txt"]

            self.node.rename_file(self.target) if rename else self.node.copy_file(self.target)

            assert not self.link.exists()
            assert not self.file.exists() if rename else self.file.exists()
            assert self.modified_file.exists()
            assert not self.modified_link.exists()
            assert self.modified_file.read_text() == content

    def test_copy_and_rename_file(self, tmp_path: Path):
        for rename, target_is_link in itertools.product([True, False], repeat=2):
            self._set_up(tmp_path, target_is_link)
            self._checks_behavior(rename, target_is_link)
            shutil.rmtree(tmp_path / "my-study")
