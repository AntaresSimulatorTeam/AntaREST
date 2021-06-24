import os
import shutil
from abc import ABC, abstractmethod
from typing import Optional, List

from antarest.common.custom_types import JSON, SUB_JSON
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.lazy_node import LazyNode


class MatrixNode(LazyNode[JSON, JSON, JSON], ABC):
    def __init__(self, context: ContextServer, config: StudyConfig) -> None:
        LazyNode.__init__(self, context, config, url_prefix="")

    def save(self, data: SUB_JSON, url: Optional[List[str]] = None) -> None:
        self._assert_url_end(url)

        if self.context.resolver.is_managed(self.config.study_id):
            if isinstance(data, dict):
                id = self.context.matrix.create(data)
                data = self.context.resolver.build_matrix_uri(id)

            link_path = self.get_link_path()
            link_path.write_text(data)
            self.config.path.unlink()
            return None

        if isinstance(data, str) and f"matrix://" in data:
            src = self.context.resolver.resolve(data)
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
    ) -> JSON:
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
    def dump(self, data: JSON, url: Optional[List[str]] = None) -> None:
        """
        Store data on tree.

        Args:
            data: new data to save
            url: data path to change

        Returns:

        """
        raise NotImplementedError()
