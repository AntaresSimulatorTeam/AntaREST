import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Union

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.exceptions import (
    DenormalizationException,
)
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import (
    LazyNode,
)

logger = logging.getLogger(__name__)


class MatrixNode(LazyNode[Union[bytes, JSON], Union[bytes, JSON], JSON], ABC):
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

        matrix = self.parse()

        uuid = self.context.matrix.create(matrix["data"])
        self.get_link_path().write_text(
            self.context.resolver.build_matrix_uri(uuid)
        )
        self.config.path.unlink()

    def denormalize(self) -> None:
        if self.config.path.exists() or not self.get_link_path().exists():
            return

        uuid = self.get_link_path().read_text()
        matrix = self.context.resolver.resolve(uuid)
        if not matrix or not isinstance(matrix, dict):
            raise DenormalizationException(
                f"Failed to retrieve original matrix for {self.config.path}"
            )

        self.dump(matrix)
        self.get_link_path().unlink()

    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> Union[bytes, JSON]:
        if not formatted:
            if self.config.path.exists():
                return self.config.path.read_bytes()

            logger.warning(f"Missing file {self.config.path}")
            return b""

        return self.parse()

    @abstractmethod
    def parse(self) -> JSON:
        """
        Parse the matrix content
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
