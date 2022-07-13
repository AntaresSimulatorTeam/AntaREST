import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union, Any

import pandas as pd  # type: ignore

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
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        freq: str,
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
        if self.get_link_path().exists() or self.config.zip_path:
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

        logger.info(f"Denormalizing matrix {self.config.path}")
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
        file_path, tmp_dir = self._get_real_file_path()
        if not formatted:
            if file_path.exists():
                return file_path.read_bytes()

            logger.warning(f"Missing file {self.config.path}")
            if tmp_dir:
                tmp_dir.cleanup()
            return b""

        return self.parse(file_path, tmp_dir)

    @abstractmethod
    def parse(
        self,
        file_path: Optional[Path] = None,
        tmp_dir: Any = None,
        return_dataframe: bool = False,
    ) -> Union[JSON, pd.DataFrame]:
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
