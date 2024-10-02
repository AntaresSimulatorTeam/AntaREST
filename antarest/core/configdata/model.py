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

from enum import Enum
from typing import Any, Optional

from sqlalchemy import Column, Integer, String  # type: ignore

from antarest.core.persistence import Base
from antarest.core.serialization import AntaresBaseModel


class ConfigDataDTO(AntaresBaseModel):
    key: str
    value: Optional[str]


class ConfigData(Base):  # type: ignore
    __tablename__ = "configdata"
    owner = Column(Integer(), primary_key=True)
    key = Column(String(), primary_key=True)
    value = Column(String(), nullable=True)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ConfigData):
            return False
        return bool(other.key == self.key and other.value == self.value and other.owner == self.owner)

    def __repr__(self) -> str:
        return f"key={self.key}, value={self.value}, owner={self.owner}"

    def to_dto(self) -> ConfigDataDTO:
        return ConfigDataDTO(key=self.key, value=self.value)


# APP MAIN CONFIG KEYS
class ConfigDataAppKeys(str, Enum):
    MAINTENANCE_MODE = "MAINTENANCE_MODE"
    MESSAGE_INFO = "MESSAGE_INFO"
