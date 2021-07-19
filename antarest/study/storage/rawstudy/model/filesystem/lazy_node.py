from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Generic, Union, cast

from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.context import ContextServer
from antarest.storage.business.rawstudy.model.filesystem.inode import INode, S, G, V


class LazyNode(INode, ABC, Generic[G, S, V]):  # type: ignore
    """
    Abstract left with implemented a lazy loading for its daughter implementation.
    """

    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
    ) -> None:
        self.context = context
        self.config = config

    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> Union[str, G]:
        self._assert_url_end(url)

        if self.get_link_path().exists():
            link = self.get_link_path().read_text()
            if expanded:
                return link
            else:
                return cast(G, self.context.resolver.resolve(link))

        if expanded:
            return self.get_lazy_content()
        else:
            return self.load(url, depth, expanded)

    def get_link_path(self) -> Path:
        path = self.config.path.parent / (self.config.path.name + ".link")
        return path

    def save(
        self, data: Union[str, bytes, S], url: Optional[List[str]] = None
    ) -> None:
        self._assert_url_end(url)

        if isinstance(data, str) and self.context.resolver.resolve(data):
            self.get_link_path().write_text(data)
            if self.config.path.exists():
                self.config.path.unlink()
            return None

        self.dump(cast(S, data), url)
        if self.get_link_path().exists():
            self.get_link_path().unlink()
        return None

    def get_lazy_content(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return f"file://{self.config.path.name}"

    @abstractmethod
    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> G:
        """
        Fetch data on disk.

        Args:
            url: data path to retrieve
            depth: after url is reached, node expand tree until matches depth asked
            expanded: context parameter to determine if current node become from a expansion

        Returns:

        """
        raise NotImplementedError()

    @abstractmethod
    def dump(self, data: S, url: Optional[List[str]] = None) -> None:
        """
        Store data on tree.

        Args:
            data: new data to save
            url: data path to change

        Returns:

        """
        raise NotImplementedError()
