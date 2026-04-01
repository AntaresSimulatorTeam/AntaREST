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
from pathlib import Path


def find_mode_dir(output_dir: Path) -> Path | None:
    for mode_name in ("economy", "adequacy"):
        mode_dir = output_dir / mode_name
        if mode_dir.exists():
            return mode_dir
    return None
