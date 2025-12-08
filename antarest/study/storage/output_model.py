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
import gzip
import uuid
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Optional, TypeAlias

from pydantic import BeforeValidator
from pydantic.alias_generators import to_camel
from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from antarest.core.persistence import Base
from antarest.core.serde import AntaresBaseModel
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency

Variables: TypeAlias = Annotated[list[str], BeforeValidator(lambda x: sorted(x))]


class AreaClusterVariables(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    name: str
    variables: Variables = []


ClusterVariables: TypeAlias = Annotated[
    list[AreaClusterVariables], BeforeValidator(lambda x: sorted(x, key=lambda a: a["name"]))
]


class AreaVariables(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    name: str
    variables: Variables = []
    thermal_clusters: ClusterVariables = []
    renewable_clusters: ClusterVariables = []
    short_term_storages: ClusterVariables = []


class LinkVariables(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    area_1_name: str
    area_2_name: str
    variables: Variables = []


class AreaAndLinkVariables(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    areas: list[AreaVariables]
    links: list[LinkVariables]


class OutputVariablesList(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    mc_ind: AreaAndLinkVariables
    mc_all: AreaAndLinkVariables


class OutputVariables(Base):
    __tablename__ = "output_variables"
    __table_args__ = (PrimaryKeyConstraint("study_id", "output_id"),)

    study_id: Mapped[str] = mapped_column(String(36), ForeignKey("study.id"), nullable=False)
    output_id: Mapped[str] = mapped_column(String, nullable=False)
    variables_list_version: Mapped[int] = mapped_column(Integer, nullable=False)
    variables_list: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    def to_model(self) -> OutputVariablesList:
        return OutputVariablesList.model_validate_json(gzip.decompress(self.variables_list))

    @staticmethod
    def from_model(study_id: str, output_id: str, variables_list: OutputVariablesList) -> "OutputVariables":
        compressed_content = gzip.compress(variables_list.model_dump_json().encode("utf-8"))
        return OutputVariables(
            study_id=study_id,
            output_id=output_id,
            variables_list_version=1,
            variables_list=compressed_content,
        )


class OutputVariablesInformation(AntaresBaseModel, extra="forbid"):
    area: list[str]
    link: list[str]

    @staticmethod
    def from_variables_list(variables_list: OutputVariablesList) -> "OutputVariablesInformation":
        args = {}

        # Areas
        all_area_variables = set()
        for area in variables_list.mc_ind.areas:
            all_area_variables.update(area.variables)
        args["area"] = sorted(all_area_variables)

        # Links
        all_link_variables = set()
        for link in variables_list.mc_ind.links:
            all_link_variables.update(link.variables)
        args["link"] = sorted(all_link_variables)

        return OutputVariablesInformation.model_validate(args)


class OutputVariablesType(StrEnum):
    AREA = "area"
    LINK = "link"
    THERMAL = "thermal"
    RENEWABLE = "renewable"
    SHORT_TERM_STORAGE = "st_storage"


class OutputVariablesViewsModel(Base):
    __tablename__ = "output_variables_views"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True)
    study_id: Mapped[str] = mapped_column(String(36), ForeignKey("study.id"), nullable=False)
    output_id: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[OutputVariablesType] = mapped_column(Enum(OutputVariablesType), nullable=False)
    frequency: Mapped[MatrixFrequency] = mapped_column(Enum(MatrixFrequency), nullable=False)
    variable_name: Mapped[str] = mapped_column(String, nullable=False)
    area_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    area_from_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    area_to_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    thermal_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    renewable_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    st_storage_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    matrix_id: Mapped[str] = mapped_column(String, ForeignKey("matrix.id"), nullable=False)
    last_read: Mapped[datetime] = mapped_column(DateTime)
