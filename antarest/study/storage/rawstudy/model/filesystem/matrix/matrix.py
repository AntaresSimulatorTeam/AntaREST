import logging
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Union, cast

import pandas as pd

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.exceptions import DenormalizationException
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode

logger = logging.getLogger(__name__)


class MatrixFrequency(str, Enum):
    """
    An enumeration of matrix frequencies.

    Each frequency corresponds to a specific time interval for a matrix's data.
    """

    ANNUAL = "annual"
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    DAILY = "daily"
    HOURLY = "hourly"


def dump_dataframe(df: pd.DataFrame, path: Path, float_format: Optional[str] = "%.6f") -> None:
    if df.empty:
        path.write_bytes(b"")
    else:
        df.to_csv(
            path,
            sep="\t",
            header=False,
            index=False,
            float_format=float_format,
        )


class MatrixNode(LazyNode[Union[bytes, JSON], Union[bytes, JSON], JSON], ABC):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        freq: MatrixFrequency,
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
        # noinspection SpellCheckingInspection
        """
        Normalize the matrix by creating a link to the normalized version.
        The original matrix is then deleted.

        Skips the normalization process if the link path already exists
        or the matrix is zipped.

        Raises:
            DenormalizationException: if the original matrix retrieval fails.
        """
        if self.get_link_path().exists() or self.config.zip_path:
            return

        matrix = self.parse(format="json")
        assert isinstance(matrix, dict)

        if "data" in matrix:
            data = cast(List[List[float]], matrix["data"])
            uuid = self.context.matrix.create(data)
            self.get_link_path().write_text(self.context.resolver.build_matrix_uri(uuid))
            self.config.path.unlink()

    def denormalize(self) -> None:
        """
        Read the matrix ID from the matrix link, retrieve the original matrix
        and write the matrix data to the file specified by `self.config.path`
        before removing the link file.
        """
        if self.config.path.exists() or not self.get_link_path().exists():
            return

        # noinspection SpellCheckingInspection
        logger.info(f"Denormalizing matrix {self.config.path}")
        uuid = self.get_link_path().read_text()
        matrix = self.context.resolver.resolve(uuid, format="json")
        if not matrix or not isinstance(matrix, dict):
            raise DenormalizationException(f"Failed to retrieve original matrix for {self.config.path}")

        self.dump(matrix)
        self.get_link_path().unlink()

    def load(  # type: ignore
        self, url: Optional[List[str]] = None, depth: int = -1, expanded: bool = False, format: Optional[str] = None
    ) -> Union[bytes, JSON, pd.DataFrame]:
        file_path, tmp_dir = self._get_real_file_path()
        if not format:
            if file_path.exists():
                return file_path.read_bytes()

            logger.warning(f"Missing file {self.config.path}")
            if tmp_dir:
                tmp_dir.cleanup()
            return b""

        result = self.parse(file_path, tmp_dir, False, format)
        if format == "json":
            return cast(JSON, result)
        return result

    @abstractmethod
    def parse(
        self,
        file_path: Optional[Path] = None,
        tmp_dir: Any = None,
        return_dataframe: bool = False,
        format: Optional[str] = None,
    ) -> Union[JSON, bytes, pd.DataFrame]:
        """
        Parse the matrix content
        """
        raise NotImplementedError()

    def dump(
        self,
        data: Union[bytes, JSON],
        url: Optional[List[str]] = None,
    ) -> None:
        """
        Write matrix data to file.

        If the input data is of type bytes, write the data to file as is.
        Otherwise, convert the data to a Pandas DataFrame and write it to file as a tab-separated CSV.
        If the resulting DataFrame is empty, write an empty bytes object to file.

        Args:
            data: The data to write to file. If data is bytes, it will be written directly to file,
                otherwise it will be converted to a Pandas DataFrame and then written to file.
            url: node URL (not used here).
        """
        self.config.path.parent.mkdir(exist_ok=True, parents=True)
        if isinstance(data, bytes):
            self.config.path.write_bytes(data)
        else:
            df = pd.DataFrame(**data)
            dump_dataframe(df, self.config.path)
