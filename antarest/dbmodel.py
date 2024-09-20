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

# noinspection PyUnresolvedReferences
from antarest.core.configdata import model as configdatamodel

# noinspection PyUnresolvedReferences
from antarest.core.filetransfer import model as filetransfermodel

# noinspection PyUnresolvedReferences
from antarest.core.persistence import Base as PersistenceBase

# noinspection PyUnresolvedReferences
from antarest.core.tasks import model as tasksmodel

# noinspection PyUnresolvedReferences
from antarest.launcher import model as launchermodel

# noinspection PyUnresolvedReferences
from antarest.login import model as loginmodel

# noinspection PyUnresolvedReferences
from antarest.matrixstore import model as matrixstoremodel

# noinspection PyUnresolvedReferences
from antarest.study import model as studymodel

# noinspection PyUnresolvedReferences
from antarest.study.storage.variantstudy.model import dbmodel as variantmodel

Base = PersistenceBase
