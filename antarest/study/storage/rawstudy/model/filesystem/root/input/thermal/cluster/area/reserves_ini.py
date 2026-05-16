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
import os
import tempfile
import zipfile
from pathlib import Path
from typing import cast

import py7zr
from filelock import FileLock
from typing_extensions import override

from antarest.core.exceptions import ShouldNotHappenException
from antarest.core.model import JSON, SUB_JSON
from antarest.core.serde.ini_reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode, IniFileNodeWarning


class InputThermalClustersAreaReservesIni(IniFileNode):
    def __init__(self, config: FileStudyTreeConfig):
        IniFileNode.__init__(self, config)

    @property
    def _reader(self) -> IniReader:
        return cast(IniReader, self.reader)

    @override
    def get(
        self,
        url: list[str] | None = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> SUB_JSON:
        if url:
            raise ValueError(f"InputThermalClustersAreaReservesIni does not support sub-path access; got {url!r}")
        if depth == 0:
            return []
        if depth <= -1 and expanded:
            return f"json://{self.config.path.name}"

        if self.config.archive_path:
            inside_archive_path = self.config.path.relative_to(self.config.archive_path.with_suffix("")).as_posix()
            if self.config.archive_path.suffix == ".zip":
                with zipfile.ZipFile(self.config.archive_path, mode="r") as zipped_folder:
                    with io.TextIOWrapper(zipped_folder.open(inside_archive_path)) as f:
                        sections = self._reader.read_repeating_sections(f)
            elif self.config.archive_path.suffix == ".7z":
                with py7zr.SevenZipFile(self.config.archive_path, mode="r") as zipped_folder:
                    with io.TextIOWrapper(zipped_folder.read([inside_archive_path])[inside_archive_path]) as f:
                        sections = self._reader.read_repeating_sections(f)
            else:
                raise ShouldNotHappenException(f"Unsupported archived study format: {self.config.archive_path.suffix}")
        else:
            sections = self._reader.read_repeating_sections(self.path)

        return cast(SUB_JSON, sections)

    @override
    def save(self, data: SUB_JSON, url: list[str] | None = None) -> None:
        self._assert_not_in_zipped_file()
        if url:
            raise ValueError(f"InputThermalClustersAreaReservesIni does not support sub-path writes; got {url!r}")
        if not isinstance(data, list):
            raise ValueError(
                f"InputThermalClustersAreaReservesIni expects a list of (section, content) tuples; got {type(data).__name__}"
            )
        sections: list[tuple[str, JSON]] = data
        with FileLock(
            str(
                Path(tempfile.gettempdir())
                / f"{self.config.study_id}-{self.path.relative_to(self.config.study_path).name.replace(os.sep, '.')}.lock"
            )
        ):
            self.writer.write_repeating_sections(sections, self.path)

    @override
    def delete(self, url: list[str] | None = None) -> None:
        if url:
            raise IniFileNodeWarning(f"Cannot delete {url!r} from reserves.ini: only whole-file deletion is supported")
        if self.path.exists():
            self.path.unlink()
