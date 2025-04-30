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

from antarest.core.persistence import Base as PersistenceBase
from antarest.core.tasks.model import TaskJob  # noqa: F401
from antarest.launcher.model import JobResult  # noqa: F401
from antarest.login.model import Identity  # noqa: F401

Base = PersistenceBase
