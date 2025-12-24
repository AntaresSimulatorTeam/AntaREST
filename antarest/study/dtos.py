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

from pathlib import Path
from typing import Dict, List, Optional

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.binding_constraint_model import BindingConstraint
from antarest.study.business.model.district_model import District
from antarest.study.model import StudyVersionInt
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    AreaConfig,
    EnrModelling,
    FileStudyTreeConfig,
    Simulation,
)


class StudyDataSynthesis(AntaresBaseModel):
    """
    Synthetic data about the **input** data of a study.
    """

    study_path: Path
    path: Path
    study_id: str
    version: StudyVersionInt
    output_path: Optional[Path] = None
    districts: Dict[str, District] = {}
    areas: Dict[str, AreaConfig] = {}
    bindings: List[BindingConstraint] = []
    store_new_set: bool = False
    archive_input_series: List[str] = []
    enr_modelling: EnrModelling = EnrModelling.AGGREGATED
    archive_path: Optional[Path] = None

    @classmethod
    def from_study_config(cls, config: FileStudyTreeConfig) -> "StudyDataSynthesis":
        return StudyDataSynthesis.model_construct(
            study_path=config.study_path,
            path=config.path,
            study_id=config.study_id,
            version=config.version,
            output_path=config.output_path,
            areas=config.areas,
            districts=config.districts,
            bindings=config.bindings,
            store_new_set=config.store_new_set,
            archive_input_series=config.archive_input_series,
            enr_modelling=EnrModelling(config.enr_modelling),
            archive_path=config.archive_path,
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

    study_path: Path
    path: Path
    study_id: str
    version: StudyVersionInt
    output_path: Optional[Path] = None
    districts: Dict[str, District] = {}
    areas: Dict[str, AreaConfig] = {}
    outputs: Dict[str, Simulation] = {}
    bindings: List[BindingConstraint] = []
    store_new_set: bool = False
    archive_input_series: List[str] = []
    enr_modelling: EnrModelling = EnrModelling.AGGREGATED
    archive_path: Optional[Path] = None

    @classmethod
    def aggregate(cls, synthesis: StudyDataSynthesis, output: list[Simulation]) -> "StudySynthesis":
        return StudySynthesis.model_construct(
            study_path=synthesis.study_path,
            path=synthesis.path,
            study_id=synthesis.study_id,
            version=synthesis.version,
            output_path=synthesis.output_path,
            areas=synthesis.areas,
            districts=synthesis.districts,
            bindings=synthesis.bindings,
            store_new_set=synthesis.store_new_set,
            archive_input_series=synthesis.archive_input_series,
            enr_modelling=synthesis.enr_modelling,
            archive_path=synthesis.archive_path,
            outputs={output.name: output for output in output},
        )
