# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
from typing import Any


class ILauncherExtension(ABC):
    @abstractmethod
    def get_name(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def after_export_flat_hook(
        self,
        job_id: str,
        study_id: str,
        study_export_path: Path,
        ext_opts: Any,
    ) -> None:
        pass

    @abstractmethod
    def before_import_hook(
        self,
        job_id: str,
        study_id: str,
        study_output_path: Path,
        ext_opts: Any,
    ) -> None:
        pass
