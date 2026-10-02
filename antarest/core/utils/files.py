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
import uuid
from collections.abc import Generator
from pathlib import Path


@contextlib.contextmanager
def temp_file_path(dir: Path) -> Generator[Path, None, None]:
    """
    Returns a temporary file path in dir and ensures it's deleted on exit.
    """
    file_name = str(uuid.uuid4())
    file_path = dir / file_name
    try:
        yield file_path
    finally:
        file_path.unlink(missing_ok=True)
