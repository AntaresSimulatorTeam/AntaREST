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
Object model used to read and update binding constraint configuration.
"""
from typing import Optional

from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.binding_constraint_model import BindingConstraintFrequency, BindingConstraintOperator


class BindingConstraintFileData(AntaresBaseModel):
    """
    Binding constraint data parsed from INI file.
    """

    model_config = ConfigDict(alias_generator=to_kebab_case, extra="forbid", populate_by_name=True)

    enabled: bool = True
    time_step: Optional[BindingConstraintFrequency] = Field(None, alias="type")
    operator: Optional[BindingConstraintOperator] = None
    comments: Optional[str] = None

    # Added in 8.3
    filter_year_by_year: Optional[str] = None
    filter_synthesis: Optional[str] = None

    # Added in 8.7
    group: Optional[str] = None


    def to_model(self) -> ThermalCluster:
        return ThermalCluster.model_validate(self.model_dump(exclude_none=True))

    @classmethod
    def from_model(cls, cluster: ThermalCluster) -> "ThermalClusterFileData":
        return cls.model_validate(cluster.model_dump(exclude={"id"}))


def parse_thermal_cluster(study_version: StudyVersion, data: Any) -> ThermalCluster:
    cluster = ThermalClusterFileData.model_validate(data).to_model()
    validate_thermal_cluster_against_version(study_version, cluster)
    initialize_thermal_cluster(cluster, study_version)
    return cluster


def serialize_thermal_cluster(study_version: StudyVersion, cluster: ThermalCluster) -> dict[str, Any]:
    validate_thermal_cluster_against_version(study_version, cluster)
    return ThermalClusterFileData.from_model(cluster).model_dump(mode="json", by_alias=True, exclude_none=True)
