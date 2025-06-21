# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from enum import StrEnum
from pathlib import Path
from typing import List, Optional, cast

import numpy as np
import pandas as pd
from numpy import typing as npt
from typing_extensions import override

from antarest.core.model import JSON
from antarest.core.utils.utils import StopWatch
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.inode import G, INode, S, V
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode

logger = logging.getLogger(__name__)


class MatrixFrequency(StrEnum):
    """
    An enumeration of matrix frequencies.

    Each frequency corresponds to a specific time interval for a matrix's data.
    """

    ANNUAL = "annual"
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    DAILY = "daily"
    HOURLY = "hourly"


def dump_dataframe(df: pd.DataFrame, path_or_buf: Path | io.BytesIO, float_format: Optional[str] = "%.6f") -> None:
    if df.empty and isinstance(path_or_buf, Path):
        path_or_buf.write_bytes(b"")
    else:
        df.to_csv(
            path_or_buf,
            sep="\t",
            header=False,
            index=False,
            float_format=float_format,
        )


def imports_matrix_from_bytes(data: bytes) -> Optional[npt.NDArray[np.float64]]:
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


class MatrixNode(LazyNode[bytes | JSON, bytes | JSON, JSON], ABC):
    def __init__(
        self,
        matrix_mapper: MatrixUriMapper,
        config: FileStudyTreeConfig,
        freq: MatrixFrequency,
    ) -> None:
        LazyNode.__init__(self, matrix_mapper, config)
        self.freq = freq

    @override
    def save(self, data: str | bytes | S, url: Optional[List[str]] = None) -> None:
        self._assert_not_in_zipped_file()
        self._assert_url_end(url)

        if isinstance(data, str) and self.matrix_mapper.matrix_exists(data):
            self.matrix_mapper.save_matrix(self, data)
        else:
            super().save(data, url)
            self.matrix_mapper.remove_link(self)

    @override
    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> str | G:
        output = cast("str | G", self._get(url, depth, expanded, formatted, get_node=False))
        assert not isinstance(output, INode)
        return output

    @override
    def _get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
        get_node: bool = False,
    ) -> str | G | INode[G, S, V]:
        self._assert_url_end(url)

        if get_node:
            return self

        if expanded:
            link_content = self.matrix_mapper.get_link_content(self)
            if link_content is not None:
                return link_content
            return self.get_lazy_content()

        return cast("str | G", self.load(url, depth, expanded, formatted))

    @override
    def get_lazy_content(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return f"matrixfile://{self.config.path.name}"

    @override
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
        self.matrix_mapper.normalize(self)

    @override
    def denormalize(self) -> None:
        """
        Read the matrix ID from the matrix link, retrieve the original matrix
        and write the matrix data to the file specified by `self.config.path`
        before removing the link file.
        """
        logger.info(f"Denormalizing matrix {self.config.path}")
        self.matrix_mapper.denormalize(self)

    @override
    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> bytes | JSON:
        file_path, _ = self._get_real_file_path()

        df = self.parse_as_dataframe(file_path)

        if formatted:
            stopwatch = StopWatch()
            data = cast(JSON, df.to_dict(orient="split"))
            stopwatch.log_elapsed(lambda x: logger.info(f"Matrix to dict in {x}s"))
            return data

        # The R scripts use the flag formatted=False
        if df.empty:
            return b""
        buffer = io.StringIO()
        df.to_csv(buffer, sep="\t", header=False, index=False, float_format="%.6f")
        return buffer.getvalue()  # type: ignore

    @override
    def delete(self, url: Optional[List[str]] = None) -> None:
        self._assert_url_end(url)
        self.matrix_mapper.delete(self)
        super().delete(url)

    @override
    def dump(
        self,
        data: bytes | JSON | pd.DataFrame,
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
            if isinstance(data, dict):
                df = pd.DataFrame(**data)
            else:
                df = data
            dump_dataframe(df, self.config.path)

    @abstractmethod
    def parse_as_dataframe(self, file_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Parse the matrix content and return it as a DataFrame object
        """
        raise NotImplementedError()
