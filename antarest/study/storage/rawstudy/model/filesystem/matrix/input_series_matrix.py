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
import io
import logging
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Self, TypeAlias

import numpy as np
import numpy.typing as npt
import polars as pl
from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError
from antarest.core.model import JSON
from antarest.core.serde.matrix_export import write_dataframe_in_tsv_format
from antarest.core.utils.archives import read_original_file_in_archive
from antarest.core.utils.polars import create_polars_dataframe, read_input_dataframe
from antarest.core.utils.utils import StopWatch
from antarest.matrixstore.matrix_uri_mapper import MatrixStorageContext, extract_matrix_id
from antarest.study.model import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.inode import OriginalFile
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode

logger = logging.getLogger(__name__)


MatrixSupplier: TypeAlias = Callable[[], npt.NDArray[np.float64]]
MatrixId: TypeAlias = str
MatrixContent: TypeAlias = bytes | JSON | pl.DataFrame


def _dump_dataframe(df: pl.DataFrame, path_or_buf: Path | io.BytesIO) -> None:
    if df.is_empty() and isinstance(path_or_buf, Path):
        path_or_buf.write_bytes(b"")
    else:
        df.write_csv(path_or_buf, separator="\t", include_header=False)


class InputSeriesMatrix(LazyNode[bytes | JSON, MatrixId | MatrixContent, JSON]):
    """
    Generic node to handle input matrix behavior
    """

    def __init__(
        self,
        matrix_storage_context: MatrixStorageContext,
        config: FileStudyTreeConfig,
        freq: MatrixFrequency = MatrixFrequency.HOURLY,
        nb_columns: int | None = None,
        default_empty: MatrixSupplier | None = None,  # optional only for the capacity matrix in Xpansion
        should_exist: bool = True,
    ):
        LazyNode.__init__(self, config)
        self._matrix_storage_context = matrix_storage_context
        self.freq = freq
        self.nb_columns = nb_columns
        self.default_empty = default_empty
        # Removes the .link suffix if the matrix is normalized
        self.config.path = self.config.path.parent / self.config.path.name.removesuffix(".link")
        self.should_exist = should_exist

    def _get_link_path(self) -> Path:
        return self.config.path.parent / (self.config.path.name + ".link")

    def _has_link(self) -> bool:
        return self._get_link_path().exists()

    def get_matrix_id(self) -> str | None:
        link_path = self._get_link_path()
        if link_path.exists():
            return extract_matrix_id(link_path.read_text())
        return None

    def _remove_link(self) -> None:
        link_path = self._get_link_path()
        if link_path.exists():
            link_path.unlink()

    def save_matrix(self, matrix_id: str) -> None:
        """
        Saves the matrix to underlying file.
        Assumes that it's already present in the matrix service.

        Implementation:
        - managed case: only writes the ID to "link" file
        - unmanaged case: writes the matrix content to the file
        """
        if self._matrix_storage_context.is_managed:
            link_path = self._get_link_path()
            if not link_path.parent.exists():
                link_path.parent.mkdir(parents=True)
            link_path.write_text(matrix_id)
            if self.config.path.exists():
                self.config.path.unlink()
        else:
            matrix = self._matrix_storage_context.matrix_service.get(matrix_id)
            self.dump(matrix)

    @override
    def get_lazy_content(self, url: list[str] | None = None, depth: int = -1, expanded: bool = False) -> str:
        """
        A matrix node will be represented either as matrix://<matrix-id>, if normalized,
        or matrix://<path>, if not normalized (previously was matrixfile:// in that case).
        """
        link_content = self.get_matrix_id()
        matrix_id = link_content or self.config.path.name
        return f"matrix://{matrix_id}"

    @override
    def get_matrix_nodes_to_normalize(self) -> list[Self]:
        """
        Return a list of itself if the node is not in the matrix-store. Else, return an empty list.
        """
        return [] if self.is_normalized else [self]

    @override
    def get_matrix_nodes_to_denormalize(self) -> list[Self]:
        """
        Return a list of itself if the node is in the matrix-store. Else, return an empty list.
        """
        return [self] if self.is_normalized else []

    @property
    def is_normalized(self) -> bool:
        return self._has_link()

    @override
    def load(
        self, url: list[str] | None = None, depth: int = -1, expanded: bool = False, formatted: bool = True
    ) -> JSON:
        raise NotImplementedError("Legacy method. We should use `parse_as_dataframe` from now on.")

    @override
    def delete(self, url: list[str] | None = None) -> None:
        self._assert_url_end(url)
        self._remove_link()
        super().delete(url)

    @override
    def dump(self, data: MatrixId | MatrixContent, url: list[str] | None = None) -> None:
        """
        Write matrix data to file.

        If the input data is a matrix ID, same as save_matrix.
        If the input data is of type bytes, write the data to file as is.
        Otherwise, convert the data to a Pandas DataFrame and write it to file as a tab-separated CSV.
        If the resulting DataFrame is empty, write an empty bytes object to file.

        Args:
            data: The data to write to file. If data is bytes, it will be written directly to file,
                otherwise it will be converted to a Pandas DataFrame and then written to file.
            url: node URL (not used here).
        """
        if isinstance(data, str):
            if not self._matrix_storage_context.matrix_service.exists(data):
                raise ValueError(f"Matrix {data} does not exist")
            self.save_matrix(data)
            return

        self.config.path.parent.mkdir(exist_ok=True, parents=True)
        if isinstance(data, bytes):
            self.config.path.write_bytes(data)
            self._remove_link()
        else:
            if isinstance(data, dict):
                df = pl.DataFrame(np.array(data["data"]))
            else:
                df = data
            self.write_dataframe(df)
            self._remove_link()

    def parse_as_dataframe(self) -> pl.DataFrame:
        """
        Loads underlying matrix to an actual dataframe, returning relevant default value if absent.
        """
        return self._parse_dataframe(use_default_empty=True)

    def parse_content(self) -> pl.DataFrame:
        """
        Loads underlying matrix to an actual dataframe.
        """
        return self._parse_dataframe(use_default_empty=False)

    def _parse_dataframe(self, use_default_empty: bool) -> pl.DataFrame:
        file_path = self.config.path
        stopwatch = StopWatch()
        link_content = self.get_matrix_id()
        if link_content:
            matrix = self._matrix_storage_context.matrix_service.get(link_content)
        else:
            try:
                matrix = read_input_dataframe(file_path, has_headers=False)
                matrix.columns = [str(i) for i in range(len(matrix.columns))]
            except FileNotFoundError as e:
                # Some matrices are optional and not required by the Simulator. If so, we shouldn't raise.
                if not self.should_exist:
                    if use_default_empty and self.default_empty is not None:
                        return create_polars_dataframe(self.default_empty())
                    return pl.DataFrame()
                # Otherwise, we raise a 404 'Not Found' exception.
                logger.warning(f"Matrix file'{file_path}' not found")
                study_id = self.config.study_id
                relpath = file_path.relative_to(self.config.study_path).as_posix()
                raise ChildNotFoundError(f"File '{relpath}' not found in the study '{study_id}'") from e

        if matrix.is_empty() and use_default_empty and self.default_empty is not None:
            matrix = create_polars_dataframe(self.default_empty())
        logger.debug(f"Matrix parsed in {stopwatch}s")
        return matrix

    def write_dataframe(self, df: pl.DataFrame) -> None:
        if not self.config.path.parent.exists():
            # Can happen when creating a new object and the file structure is not yet fully created
            self.config.path.parent.mkdir(parents=True)

        # If the DataFrame content corresponds to the `default_empty` attribute, we should just create an empty file.
        # This way, we can write the content quicker, and the file takes less place on the fs.
        if df.is_empty() or self.default_empty is not None and np.array_equal(df.to_numpy(), self.default_empty()):
            self.config.path.write_text("")
        else:
            write_dataframe_in_tsv_format(df, self.config.path)

        self._remove_link()

    def _infer_path(self) -> Path:
        link_path = self._get_link_path()
        if link_path.exists():
            return link_path
        elif self.config.path.exists():
            return self.config.path
        raise ChildNotFoundError(f"Neither link file {link_path} nor matrix file {self.config.path} exists")

    def rename_file(self, target: str) -> None:
        target_path = self.config.path.parent.joinpath(f"{target}{''.join(self._infer_path().suffixes)}")
        target_path.unlink(missing_ok=True)
        self._infer_path().rename(target_path)

    def copy_file(self, target: str) -> None:
        target_path = self.config.path.parent.joinpath(f"{target}{''.join(self._infer_path().suffixes)}")
        target_path.unlink(missing_ok=True)
        shutil.copy(self._infer_path(), target_path)

    @override
    def get_file_content(self) -> OriginalFile:
        suffix = self.config.path.suffix
        filename = self.config.path.name
        if self.config.archive_path:
            content = read_original_file_in_archive(
                self.config.archive_path, self.get_relative_path_inside_archive(self.config.archive_path)
            )
        elif self._has_link():
            target_path = self.config.path.with_suffix(".txt")
            buffer = io.BytesIO()
            df = self.parse_as_dataframe()
            _dump_dataframe(df, buffer)
            content = buffer.getvalue()
            suffix = target_path.suffix
            filename = target_path.name
        else:
            content = self.config.path.read_bytes()

        if content == b"" and self.default_empty is not None:
            # The file is empty, we should return the `default_empty` value
            buffer = io.BytesIO()
            _dump_dataframe(pl.DataFrame(self.default_empty()), buffer)
            content = buffer.getvalue()

        return OriginalFile(content=content, suffix=suffix, filename=filename)
