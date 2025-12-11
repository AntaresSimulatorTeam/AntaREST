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
from typing import List


class FavoriteService:
    pass

    def list_favorites(self) -> List:
        return []

    def add_favorite(self, uuid: str):
        raise NotImplementedError

    def delete_favorite(self, uuid: str):
        raise NotImplementedError
