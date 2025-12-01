# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
import contextlib
import io
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Self, TypeAlias, cast

import numpy as np
import pandas as pd
import polars as pl
from typing_extensions import override

from antarest.core.model import JSON
from antarest.core.serde.np_array import NpArray
from antarest.core.utils.utils import StopWatch
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapper
from antarest.study.model import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode

logger = logging.getLogger(__name__)


def dump_dataframe(df: pd.DataFrame, path_or_buf: Path | io.BytesIO) -> None:
    if df.empty and isinstance(path_or_buf, Path):
        path_or_buf.write_bytes(b"")
    else:
        pl.from_pandas(df).write_csv(path_or_buf, separator="\t", include_header=False)


def imports_matrix_from_bytes(data: bytes) -> Optional[NpArray]:
    """Tries to convert bytes to a numpy array when importing a matrix"""
    str_data = data.decode("utf-8")
    if not str_data:
        return np.zeros(shape=(0, 0))
    for delimiter in [",", ";", "\t"]:
        with contextlib.suppress(Exception):
            df = pd.read_csv(io.BytesIO(data), delimiter=delimiter, header=None).replace(",", ".", regex=True)
            df = df.dropna(axis=1, how="all")  # We want to remove columns full of NaN at the import
            matrix = df.to_numpy(dtype=np.float64)
            return matrix
    return None


MatrixId: TypeAlias = str
# Either raw content, or dictionary representation, or dataframe.
MatrixContent: TypeAlias = bytes | JSON | pd.DataFrame


class MatrixNode(LazyNode[bytes | JSON, MatrixId | MatrixContent, JSON], ABC):
    def __init__(
        self,
        matrix_mapper: MatrixUriMapper,
        config: FileStudyTreeConfig,
        freq: MatrixFrequency,
    ) -> None:
        LazyNode.__init__(self, matrix_mapper, config)
        self.freq = freq

    @override
    def get_lazy_content(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        link_content = self.matrix_mapper.get_link_content(self)
        if link_content is not None:
            return link_content
        return f"matrixfile://{self.config.path.name}"

    @override
    def get_matrix_nodes_to_normalize(self) -> list[Self]:
        """
        Return a list of itself if the node is not in the matrix-store. Else, return an empty list.
        """
        return [] if self.matrix_mapper.has_link(self) else [self]

    @override
    def get_matrix_nodes_to_denormalize(self) -> list[Self]:
        """
        Return a list of itself if the node is in the matrix-store. Else, return an empty list.
        """
        return [self] if self.matrix_mapper.has_link(self) else []

    @override
    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> JSON:
        """
        The only usage of formatted=False was via the R scripts inside the GET /raw endpoint.
        Now we're using the `parse_as_dataframe` method so we can always return the value as if formatted was True.
        """
        file_path, _ = self._get_real_file_path()

        df = self.parse_as_dataframe(file_path)

        stopwatch = StopWatch()
        data = cast(JSON, df.to_dict(orient="split"))
        stopwatch.log_elapsed(lambda x: logger.info(f"Matrix to dict in {x}s"))
        return data

    @override
    def delete(self, url: Optional[List[str]] = None) -> None:
        self._assert_url_end(url)
        self.matrix_mapper.delete(self)
        super().delete(url)

    @override
    def dump(
        self,
        data: MatrixId | MatrixContent,
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
        if isinstance(data, MatrixId):
            if not self.matrix_mapper.matrix_exists(data):
                raise ValueError(f"Matrix {data} does not exist")
            self.matrix_mapper.save_matrix(self, data)
            return

        self.config.path.parent.mkdir(exist_ok=True, parents=True)
        if isinstance(data, bytes):
            self.config.path.write_bytes(data)
            self.matrix_mapper.remove_link(self)
        else:
            if isinstance(data, dict):
                df = pd.DataFrame(**data)
            else:
                df = data
            self.write_dataframe(df)
            self.matrix_mapper.remove_link(self)

    @abstractmethod
    def parse_as_dataframe(self, file_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Parse the matrix content and return it as a DataFrame object
        """
        raise NotImplementedError()

    @abstractmethod
    def write_dataframe(self, df: pd.DataFrame) -> None:
        raise NotImplementedError()
