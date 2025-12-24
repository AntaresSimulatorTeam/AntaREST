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
import os
import shutil
from pathlib import Path
from typing import BinaryIO

from typing_extensions import override

from antarest.study.output.lfs.lfs import ILargeFileStorage


class DirLargeFileStorage(ILargeFileStorage):
    """
    Implementation storing files flat in a configured directory.
    """

    def __init__(self, directory: Path):
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)

    def _get_path(self, blob_id: str) -> Path:
        return self._directory / blob_id

    @override
    def read_file(self, blob_id: str, target_path: Path) -> None:
        shutil.copy(self._get_path(blob_id), target_path)

    @override
    def write_file(self, blob_id: str, source: Path | BinaryIO) -> None:
        if isinstance(source, Path):
            shutil.copy(source, self._get_path(blob_id))
        else:
            with self._get_path(blob_id).open("wb") as f:
                shutil.copyfileobj(source, f)

    @override
    def file_exists(self, blob_id: str) -> bool:
        return self._get_path(blob_id).exists()

    @override
    def delete_file(self, blob_id: str) -> None:
        self._get_path(blob_id).unlink(missing_ok=True)

    @override
    def list_files(self) -> list[str]:
        return os.listdir(self._directory)
