from abc import ABC, abstractmethod
from typing import List, Optional, Union

from antarest.core.custom_types import JSON
from antarest.matrixstore.model import MatrixDTO
from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.exceptions import (
    DenormalizationException,
)
from antarest.storage.repository.filesystem.lazy_node import LazyNode


class MatrixNode(LazyNode[JSON, Union[bytes, JSON], JSON], ABC):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig, freq: str
    ) -> None:
        LazyNode.__init__(self, context, config)
        self.freq = freq

    def get_lazy_content(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return f"matrixfile://{self.config.path.name}"

    def normalize(self) -> None:
        if self.get_link_path().exists():
            return

        matrix = self.load()
        dto = MatrixDTO(
            width=matrix["width"],
            height=matrix["height"],
            index=matrix["index"],
            columns=matrix["columns"],
            data=matrix["data"],
        )

        uuid = self.context.matrix.create(dto)
        self.get_link_path().write_text(
            self.context.resolver.build_matrix_uri(uuid)
        )
        self.config.path.unlink()

    def denormalize(self) -> None:
        if self.config.path.exists():
            return

        uuid = self.get_link_path().read_text()
        matrix = self.context.resolver.resolve(uuid)
        if not matrix or not isinstance(matrix, dict):
            raise DenormalizationException(
                f"Failed to retrieve original matrix for {self.config.path}"
            )

        self.dump(matrix)
        self.get_link_path().unlink()

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
    def _dump_json(self, data: JSON) -> None:
        """
        Store data on tree.

        Args:
            data: new data to save
            url: data path to change

        Returns:

        """

        raise NotImplementedError()

    def dump(
        self, data: Union[bytes, JSON], url: Optional[List[str]] = None
    ) -> None:
        if isinstance(data, bytes):
            self.config.path.parent.mkdir(exist_ok=True, parents=True)
            self.config.path.write_bytes(data)
        else:
            self._dump_json(data)
