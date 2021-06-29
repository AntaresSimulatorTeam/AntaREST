import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, cast

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

    def save(self, data: SUB_JSON, url: Optional[List[str]] = None) -> None:
        self._assert_url_end(url)

        if self.context.resolver.is_managed(self.config.study_id):
            if isinstance(data, dict):
                data = self._send_to_store(data)

            link_path = self.get_link_path()
            link_path.write_text(cast(str, data))
            self.config.path.unlink()
            return None

        else:
            if isinstance(data, str):
                data = self.context.resolver.resolve(data, parser=self.parse)  # type: ignore

            self.dump(cast(JSON, data))
            return None

    def _send_to_store(self, data: JSON) -> str:
        dto = MatrixDTO(
            freq=MatrixFreq.from_str(self.freq),
            index=data["index"],
            columns=data["columns"],
            data=data["data"],
        )
        id = self.context.matrix.create(dto)
        uri = self.context.resolver.build_matrix_uri(id)
        return uri

    @abstractmethod
    def parse(self, path: Path) -> JSON:
        raise NotImplementedError()

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
        return self.parse(self.config.path)

    @abstractmethod
    def format(self, data: JSON, path: Path) -> None:
        raise NotImplementedError()

    def dump(self, data: JSON, url: Optional[List[str]] = None) -> None:
        """
        Store data on tree.

        Args:
            data: new data to save
            url: data path to change

        Returns:

        """
        self.format(data, self.config.path)
