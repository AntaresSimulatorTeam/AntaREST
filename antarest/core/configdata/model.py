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

from enum import StrEnum
from typing import Any, Optional

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import mapped_column
from typing_extensions import override

from antarest.core.persistence import Base
from antarest.core.serde import AntaresBaseModel


class ConfigDataDTO(AntaresBaseModel):
    key: str
    value: Optional[str]


class ConfigData(Base):
    __tablename__ = "configdata"
    owner = mapped_column(Integer(), primary_key=True)
    key = mapped_column(String(), primary_key=True)
    value = mapped_column(String(), nullable=True)

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ConfigData):
            return False
        return bool(other.key == self.key and other.value == self.value and other.owner == self.owner)

    @override
    def __repr__(self) -> str:
        return f"key={self.key}, value={self.value}, owner={self.owner}"

    def to_dto(self) -> ConfigDataDTO:
        return ConfigDataDTO(key=self.key, value=self.value)


# APP MAIN CONFIG KEYS
class ConfigDataAppKeys(StrEnum):
    MAINTENANCE_MODE = "MAINTENANCE_MODE"
    MESSAGE_INFO = "MESSAGE_INFO"
