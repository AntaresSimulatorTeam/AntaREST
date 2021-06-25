import os
import shutil
from abc import ABC, abstractmethod
from typing import Optional, List

from antarest.common.custom_types import JSON, SUB_JSON
from antarest.matrixstore.model import MatrixDTO, MatrixFreq
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.lazy_node import LazyNode


class MatrixNode(LazyNode[JSON, JSON, JSON], ABC):
    def __init__(
        self, context: ContextServer, config: StudyConfig, freq: str
    ) -> None:
        LazyNode.__init__(self, context, config)
        self.freq = freq

    def save(self, data: JSON, url: Optional[List[str]] = None) -> None:
        self._assert_url_end(url)

        if self.context.resolver.is_managed(self.config.study_id):
            if isinstance(data, dict):
                dto = MatrixDTO(
                    freq=MatrixFreq.from_str(self.freq),
                    index=data["index"],
                    columns=data["columns"],
                    data=data["data"],
                )
                id = self.context.matrix.create(dto)
                data = self.context.resolver.build_matrix_uri(id)

            link_path = self.get_link_path()
            link_path.write_text(data)
            self.config.path.unlink()
            return None

        else:
            if isinstance(data, str) and "matrix://" in data:
                data = self.context.resolver.resolve(data)

            self.dump(data)
            return None

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
