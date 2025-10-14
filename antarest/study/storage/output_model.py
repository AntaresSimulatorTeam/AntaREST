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


from pydantic.alias_generators import to_camel
from sqlalchemy import (
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from antarest.core.persistence import Base
from antarest.core.serde import AntaresBaseModel


class AreaClusterVariables(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    name: str
    variables: list[str]


class AreaVariables(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    name: str
    variables: list[str]
    thermal_clusters: list[AreaClusterVariables]
    renewable_clusters: list[AreaClusterVariables]
    short_term_storages: list[AreaClusterVariables]


class LinkVariables(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    area_1_name: str
    area_2_name: str
    variables: list[str]


class AreaAndLinkVariables(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    areas: list[AreaVariables]
    links: list[LinkVariables]


class OutputVariablesMetadata(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    mc_ind: AreaAndLinkVariables
    mc_all: AreaAndLinkVariables


class OutputVariables(Base):
    __tablename__ = "output_variables"
    __table_args__ = (PrimaryKeyConstraint("study_id", "output_id"),)

    study_id: Mapped[str] = mapped_column(String(36), ForeignKey("study.id"), primary_key=True, nullable=False)
    output_id: Mapped[str] = mapped_column(String, nullable=False)
    variables_metadata_version: Mapped[int] = mapped_column(Integer, nullable=False)
    variables_metadata: Mapped[str] = mapped_column(String, nullable=False)

    def to_model(self) -> OutputVariablesMetadata:
        return OutputVariablesMetadata.model_validate_json(self.variables_metadata)
