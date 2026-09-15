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

from typing_extensions import override

from antarest.study.business.model.gems.library import GemsLibrary
from antarest.study.dao.api.gems_library_dao import GemsLibraryDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase


class DatabaseGemsLibraryDao(GemsLibraryDao, DatabaseDaoBase):
    """Database implementation of GemsLibraryDao"""

    @override
    def get_library(self) -> GemsLibrary:
        raise NotImplementedError()

    @override
    def save_library(self, library: GemsLibrary) -> None:
        raise NotImplementedError()
