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

from pathlib import Path
from typing import Callable

import pytest

# noinspection PyUnresolvedReferences
from tests.conftest_db import *

# noinspection PyUnresolvedReferences
from tests.conftest_instances import *

# noinspection PyUnresolvedReferences
from tests.conftest_services import *

HERE = Path(__file__).parent.resolve()
PROJECT_DIR = next(iter(p for p in HERE.parents if p.joinpath("antarest").exists()))


@pytest.fixture(scope="session")
def project_path() -> Path:
    return PROJECT_DIR


@pytest.fixture
def ini_cleaner() -> Callable[[str], str]:
    def cleaner(txt: str) -> str:
        lines = filter(None, map(str.strip, txt.splitlines(keepends=False)))
        return "\n".join(lines)

    return cleaner


@pytest.fixture
def clean_ini_writer(ini_cleaner: Callable[[str], str]) -> Callable[[Path, str], None]:
    def write_clean_ini(path: Path, txt: str) -> None:
        clean_ini = ini_cleaner(txt)
        path.write_text(clean_ini)

    return write_clean_ini
