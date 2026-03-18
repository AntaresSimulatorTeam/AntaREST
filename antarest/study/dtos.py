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

from typing import Dict, List

from antarest.core.serde import AntaresBaseModel
from antarest.output.storage.output_storage import OutputDetails
from antarest.study.business.model.binding_constraint_model import BindingConstraint
from antarest.study.business.model.config.general_model import Mode
from antarest.study.business.model.district_model import District
from antarest.study.model import StudyVersionInt
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    AreaConfig,
    EnrModelling,
    FileStudyTreeConfig,
)


class OutputSynthesis(AntaresBaseModel):
    """
    Synthetic data about outputs of a study.
    """

    name: str
    mode: Mode
    synthesis: bool
    by_year: bool
    nb_years: int
    archived: bool

    @classmethod
    def from_output_details(cls, output: OutputDetails) -> "OutputSynthesis":
        return cls(
            name=output.name,
            mode=output.mode,
            synthesis=output.synthesis,
            by_year=output.by_year,
            nb_years=output.nb_years,
            archived=output.archived,
        )


class StudyDataSynthesis(AntaresBaseModel):
    """
    Synthetic data about the **input** data of a study.
    """

    study_id: str
    version: StudyVersionInt
    districts: Dict[str, District] = {}
    areas: Dict[str, AreaConfig] = {}
    bindings: List[BindingConstraint] = []
    enr_modelling: EnrModelling = EnrModelling.AGGREGATED

    @classmethod
    def from_study_config(cls, config: FileStudyTreeConfig) -> "StudyDataSynthesis":
        return StudyDataSynthesis.model_construct(
            study_id=config.study_id,
            version=config.version,
            areas=config.areas,
            districts=config.districts,
            bindings=config.bindings,
            enr_modelling=EnrModelling(config.enr_modelling),
        )


class StudySynthesis(AntaresBaseModel):
    """
    Synthetic data about a study, including input **and** output data.

    Design note:
    lot of boiler plate duplication between this, StudyDataSynthesis and FileStudyTreeConfigDTO,
    but they represent indeed different things.
    FileStudyTreeConfigDTO is tied to the filestudy format, and should remain an internal implementation
    detail, not something exposed in the API.
    This class could be a composition of StudyDataSynthesis and outputs, but that would be
    a breaking change of the API.
    """

    study_id: str
    version: StudyVersionInt
    districts: Dict[str, District] = {}
    areas: Dict[str, AreaConfig] = {}
    outputs: Dict[str, OutputSynthesis] = {}
    bindings: List[BindingConstraint] = []
    enr_modelling: EnrModelling = EnrModelling.AGGREGATED

    @classmethod
    def aggregate(cls, synthesis: StudyDataSynthesis, outputs: dict[str, OutputDetails]) -> "StudySynthesis":
        return StudySynthesis.model_construct(
            study_id=synthesis.study_id,
            version=synthesis.version,
            areas=synthesis.areas,
            districts=synthesis.districts,
            bindings=synthesis.bindings,
            enr_modelling=synthesis.enr_modelling,
            outputs={k: OutputSynthesis.from_output_details(v) for k, v in outputs.items()},
        )
