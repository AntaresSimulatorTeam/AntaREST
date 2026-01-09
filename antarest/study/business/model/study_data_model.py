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
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.model.area_model import AreaUI
from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.business.model.binding_constraint_model import BindingConstraint
from antarest.study.business.model.config.adequacy_patch_model import AdequacyPatchParameters
from antarest.study.business.model.config.advanced_parameters_model import AdvancedParameters
from antarest.study.business.model.config.general_model import GeneralConfig
from antarest.study.business.model.config.optimization_config_model import OptimizationPreferences
from antarest.study.business.model.config.playlist_model import Playlist
from antarest.study.business.model.config.timeseries_config_model import TimeSeriesConfiguration
from antarest.study.business.model.hydro_allocation_model import HydroAllocation
from antarest.study.business.model.hydro_model import HydroProperties
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.sts_model import STStorage, STStorageAdditionalConstraint
from antarest.study.business.model.thematic_trimming_model import ThematicTrimming
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.business.model.xpansion_model import XpansionCandidate, XpansionSettings
from antarest.study.model import StudyVersionStr


class StudySettingsDTO(AntaresBaseModel, alias_generator=to_camel, populate_by_name=True):
    time_series: TimeSeriesConfiguration
    general: GeneralConfig
    advanced_parameters: AdvancedParameters
    adequacy_patch: AdequacyPatchParameters
    optimization: OptimizationPreferences
    thematic_trimming: ThematicTrimming
    playlist: Playlist


class XpansionConstraintSign(EnumIgnoreCase):
    LESS_OR_EQUAL = "less_or_equal"
    GREATER_OR_EQUAL = "greater_or_equal"
    EQUAL = "equal"


class XpansionConstraint(AntaresBaseModel, alias_generator=to_camel, populate_by_name=True):
    name: str
    sign: XpansionConstraintSign
    right_hand_side: float
    candidates_coefficients: dict[str, float] = {}


class StudyXpansionDTO(AntaresBaseModel, alias_generator=to_camel, populate_by_name=True):
    settings: XpansionSettings
    candidates: list[XpansionCandidate]
    constraints: list[XpansionConstraint]


class StudyShortTermStorageDTO(STStorage, alias_generator=to_camel, populate_by_name=True):
    constraints: list[STStorageAdditionalConstraint]


class StudyHydroDTO(HydroProperties, alias_generator=to_camel, populate_by_name=True):
    allocation: HydroAllocation


class StudyAreasDTO(AntaresBaseModel, alias_generator=to_camel, populate_by_name=True):
    id: str
    name: str
    properties: AreaProperties
    ui: AreaUI
    thermals: list[ThermalCluster]
    renewables: list[RenewableCluster]
    st_storages: list[StudyShortTermStorageDTO]
    hydro: StudyHydroDTO


class StudyMetaDataDTO(AntaresBaseModel, alias_generator=to_camel, populate_by_name=True):
    name: str
    version: StudyVersionStr
    folder: str | None


class StudyDataDTO(AntaresBaseModel, alias_generator=to_camel, populate_by_name=True):
    """
    DTO representing data of the whole study.
    """

    metadata: StudyMetaDataDTO
    areas: list[StudyAreasDTO]
    links: list[Link]
    binding_constraints: list[BindingConstraint]
    settings: StudySettingsDTO
    xpansion: StudyXpansionDTO | None
