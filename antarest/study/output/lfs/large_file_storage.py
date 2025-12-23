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
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO


class ILargeFileStorage(ABC):
    """
    Interface for storing large files, possibly larger than memory.

    Relies on paths for the moment, could use streams if needed
    """

    @abstractmethod
    def read_file(self, blob_id: str, target_path: Path) -> None:
        raise NotImplementedError()

    @abstractmethod
    def write_file(self, blob_id: str, source: Path | BinaryIO) -> None:
        raise NotImplementedError()

    @abstractmethod
    def file_exists(self, blob_id: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def delete_file(self, blob_id: str) -> None:
        raise NotImplementedError()
