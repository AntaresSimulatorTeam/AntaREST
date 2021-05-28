import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Generic

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.inode import INode, S, G, V


class LazyNode(INode, ABC, Generic[G, S, V]):  # type: ignore
    def __init__(self) -> None:
        self.config = StudyConfig(study_path=Path())

    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> G:
        self._assert_url(url)
        if expanded:
            path = str(self.config.path.absolute()).replace("\\", "/")
            return f"file://{path}"  # type: ignore

        return self.load(url, depth, expanded)

    def save(self, data: S, url: Optional[List[str]] = None) -> None:
        self._assert_url(url)

        if isinstance(data, str) and "file://" in data:
            src = Path(data[len("file://") :])
            print(f"{src} == {self.config.path}")
            if src != self.config.path:
                self.config.path.parent.mkdir(exist_ok=True, parents=True)
                shutil.copyfile(src, self.config.path)
            return None

        return self.dump(data, url)

    @abstractmethod
    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> G:
        raise NotImplementedError()

    @abstractmethod
    def dump(self, data: S, url: Optional[List[str]] = None) -> None:
        raise NotImplementedError()
