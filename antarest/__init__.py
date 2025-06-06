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

"""
Antares Web

This module contains the project metadata.
"""

from pathlib import Path

# Standard project metadata

__version__ = "2.21.0"
__author__ = "RTE, Antares Web Team"
__date__ = "2025-05-26"
# noinspection SpellCheckingInspection
__credits__ = "(c) Réseau de Transport de l’Électricité (RTE)"

ROOT_DIR: Path = Path(__file__).resolve().parent
