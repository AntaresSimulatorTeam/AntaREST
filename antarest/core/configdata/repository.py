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

from operator import and_
from typing import Optional

from sqlalchemy import select

from antarest.core.configdata.model import ConfigData
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import JSON
from antarest.core.serde.json import from_json, to_json_string
from antarest.core.utils.fastapi_sqlalchemy import db


class ConfigDataRepository:
    def save(self, configdata: ConfigData) -> ConfigData:
        configdata = db.session.merge(configdata)
        db.session.add(configdata)
        db.session.commit()
        return configdata

    def get(self, key: str, owner: Optional[int] = None) -> Optional[ConfigData]:
        return db.session.execute(
            select(ConfigData).where(
                and_(
                    ConfigData.owner == (owner or DEFAULT_ADMIN_USER.id),
                    ConfigData.key == key,
                )
            )
        ).scalar_one_or_none()

    def get_json(self, key: str, owner: Optional[int] = None) -> Optional[JSON]:
        configdata = self.get(key, owner)
        if configdata:
            data: JSON = from_json(configdata.value)
            return data
        return None

    def put_json(self, key: str, data: JSON, owner: Optional[int] = None) -> None:
        configdata = ConfigData(
            key=key,
            value=to_json_string(data),
            owner=owner or DEFAULT_ADMIN_USER.id,
        )
        configdata = db.session.merge(configdata)
        db.session.add(configdata)
        db.session.commit()
