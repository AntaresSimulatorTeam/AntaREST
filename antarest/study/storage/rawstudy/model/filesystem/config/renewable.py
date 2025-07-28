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

from typing import Any, Optional

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.renewable_cluster_model import (
    RenewableCluster,
    RenewableClusterGroup,
    TimeSeriesInterpretation,
    validate_renewable_cluster_against_version,
)


class RenewableClusterFileData(AntaresBaseModel):
    """
    Renewable cluster data parsed from INI file.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    enabled: Optional[bool] = None
    unit_count: Optional[int] = Field(default=None, alias="unitcount")
    nominal_capacity: Optional[float] = Field(default=None, alias="nominalcapacity")
    group: Optional[RenewableClusterGroup] = None
    ts_interpretation: Optional[TimeSeriesInterpretation] = Field(default=None, alias="ts-interpretation")

    def to_model(self) -> RenewableCluster:
        return RenewableCluster.model_validate(self.model_dump(exclude_none=True))

    @classmethod
    def from_model(cls, cluster: RenewableCluster) -> "RenewableClusterFileData":
        return cls.model_validate(cluster.model_dump(exclude={"id"}))


def parse_renewable_cluster(study_version: StudyVersion, data: Any) -> RenewableCluster:
    cluster = RenewableClusterFileData.model_validate(data).to_model()
    validate_renewable_cluster_against_version(study_version, cluster)
    return cluster


def serialize_renewable_cluster(study_version: StudyVersion, cluster: RenewableCluster) -> dict[str, Any]:
    validate_renewable_cluster_against_version(study_version, cluster)
    return RenewableClusterFileData.from_model(cluster).model_dump(mode="json", by_alias=True, exclude_none=True)
