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

import enum
import re
import typing as t

from pydantic import Field

from antarest.core.serialization import AntaresBaseModel
from antarest.study.business.all_optional_meta import all_optional_model, camel_case_model
from antarest.study.model import PatchArea, PatchCluster
from antarest.study.storage.rawstudy.model.filesystem.config.area import (
    AdequacyPathProperties,
    AreaFolder,
    OptimizationProperties,
    UIProperties,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class AreaType(enum.Enum):
    AREA = "AREA"
    DISTRICT = "DISTRICT"


class AreaCreationDTO(AntaresBaseModel):
    name: str
    type: AreaType
    metadata: t.Optional[PatchArea] = None
    set: t.Optional[t.List[str]] = None


# review: is this class necessary?
class ClusterInfoDTO(PatchCluster):
    id: str
    name: str
    enabled: bool = True
    unitcount: int = 0
    nominalcapacity: float = 0
    group: t.Optional[str] = None
    min_stable_power: t.Optional[float] = None
    min_up_time: t.Optional[int] = None
    min_down_time: t.Optional[int] = None
    spinning: t.Optional[float] = None
    marginal_cost: t.Optional[float] = None
    spread_cost: t.Optional[float] = None
    market_bid_cost: t.Optional[float] = None


class AreaInfoDTO(AreaCreationDTO):
    id: str
    thermals: t.Optional[t.List[ClusterInfoDTO]] = None


class LayerInfoDTO(AntaresBaseModel):
    id: str
    name: str
    areas: t.List[str]


class UpdateAreaUi(AntaresBaseModel, extra="forbid", populate_by_name=True):
    """
    DTO for updating area UI

    Usage:

    >>> from antarest.study.business.model.area_model import UpdateAreaUi
    >>> from pprint import pprint

    >>> obj = {
    ...     "x": -673.75,
    ...     "y": 301.5,
    ...     "color_rgb": [230, 108, 44],
    ...     "layerX": {"0": -230, "4": -230, "6": -95, "7": -230, "8": -230},
    ...     "layerY": {"0": 136, "4": 136, "6": 39, "7": 136, "8": 136},
    ...     "layerColor": {
    ...         "0": "230, 108, 44",
    ...         "4": "230, 108, 44",
    ...         "6": "230, 108, 44",
    ...         "7": "230, 108, 44",
    ...         "8": "230, 108, 44",
    ...     },
    ... }

    >>> model = UpdateAreaUi(**obj)
    >>> pprint(model.model_dump(by_alias=True), width=80)
    {'colorRgb': [230, 108, 44],
     'layerColor': {0: '230, 108, 44',
                    4: '230, 108, 44',
                    6: '230, 108, 44',
                    7: '230, 108, 44',
                    8: '230, 108, 44'},
     'layerX': {0: -230, 4: -230, 6: -95, 7: -230, 8: -230},
     'layerY': {0: 136, 4: 136, 6: 39, 7: 136, 8: 136},
     'x': -673,
     'y': 301}

    """

    x: int = Field(title="X position")
    y: int = Field(title="Y position")
    color_rgb: t.Sequence[int] = Field(title="RGB color", alias="colorRgb")
    layer_x: t.Mapping[int, int] = Field(default_factory=dict, title="X position of each layer", alias="layerX")
    layer_y: t.Mapping[int, int] = Field(default_factory=dict, title="Y position of each layer", alias="layerY")
    layer_color: t.Mapping[int, str] = Field(default_factory=dict, title="Color of each layer", alias="layerColor")


def _get_ui_info_map(file_study: FileStudy, area_ids: t.Sequence[str]) -> t.Dict[str, t.Any]:
    """
    Get the UI information (a JSON object) for each selected Area.

    Args:
        file_study: A file study from which the configuration can be read.
        area_ids: List of selected area IDs.

    Returns:
        Dictionary where keys are IDs, and values are UI objects.

    Raises:
        ChildNotFoundError: if one of the Area IDs is not found in the configuration.
    """
    # If there is no ID, it is better to return an empty dictionary
    # instead of raising an obscure exception.
    if not area_ids:
        return {}

    ui_info_map = file_study.tree.get(["input", "areas", ",".join(area_ids), "ui"])

    # If there is only one ID in the `area_ids`, the result returned from
    # the `file_study.tree.get` call will be a single UI object.
    # On the other hand, if there are multiple values in `area_ids`,
    # the result will be a dictionary where the keys are the IDs,
    # and the values are the corresponding UI objects.
    if len(area_ids) == 1:
        ui_info_map = {area_ids[0]: ui_info_map}

    # Convert to UIProperties to ensure that the UI object is valid.
    ui_info_map = {area_id: UIProperties(**ui_info).to_config() for area_id, ui_info in ui_info_map.items()}

    return ui_info_map


def _get_area_layers(area_uis: t.Dict[str, t.Any], area: str) -> t.List[str]:
    if area in area_uis and "ui" in area_uis[area] and "layers" in area_uis[area]["ui"]:
        return re.split(r"\s+", (str(area_uis[area]["ui"]["layers"]) or ""))
    return []


# noinspection SpellCheckingInspection
class _BaseAreaDTO(
    OptimizationProperties.FilteringSection,
    OptimizationProperties.ModalOptimizationSection,
    AdequacyPathProperties.AdequacyPathSection,
    extra="forbid",
    validate_assignment=True,
    populate_by_name=True,
):
    """
    Represents an area output.

    Aggregates the fields of the `OptimizationProperties` and `AdequacyPathProperties` classes,
    but without the `UIProperties` fields.

    Add the fields extracted from the `/input/thermal/areas.ini` information:

    - `average_unsupplied_energy_cost` is extracted from `unserverd_energy_cost`,
    - `average_spilled_energy_cost` is extracted from `spilled_energy_cost`.
    """

    average_unsupplied_energy_cost: float = Field(0.0, description="average unserverd energy cost (€/MWh)")
    average_spilled_energy_cost: float = Field(0.0, description="average spilled energy cost (€/MWh)")


# noinspection SpellCheckingInspection
@all_optional_model
@camel_case_model
class AreaOutput(_BaseAreaDTO):
    """
    DTO object use to get the area information using a flat structure.
    """

    @classmethod
    def from_model(
        cls,
        area_folder: AreaFolder,
        *,
        average_unsupplied_energy_cost: float,
        average_spilled_energy_cost: float,
    ) -> "AreaOutput":
        """
        Creates a `GetAreaDTO` object from configuration data.

        Args:
            area_folder: Configuration data read from the `/input/areas/<area>` information.
            average_unsupplied_energy_cost: Unserverd energy cost (€/MWh).
            average_spilled_energy_cost: Spilled energy cost (€/MWh).
        Returns:
            The `GetAreaDTO` object.
        """
        obj = {
            "average_unsupplied_energy_cost": average_unsupplied_energy_cost,
            "average_spilled_energy_cost": average_spilled_energy_cost,
            **area_folder.optimization.filtering.model_dump(mode="json", by_alias=False),
            **area_folder.optimization.nodal_optimization.model_dump(mode="json", by_alias=False),
            # adequacy_patch is only available if study version >= 830.
            **(
                area_folder.adequacy_patch.adequacy_patch.model_dump(mode="json", by_alias=False)
                if area_folder.adequacy_patch
                else {}
            ),
        }
        return cls(**obj)

    def _to_optimization(self) -> OptimizationProperties:
        obj = {name: getattr(self, name) for name in OptimizationProperties.FilteringSection.model_fields}
        filtering_section = OptimizationProperties.FilteringSection(**obj)
        obj = {name: getattr(self, name) for name in OptimizationProperties.ModalOptimizationSection.model_fields}
        nodal_optimization_section = OptimizationProperties.ModalOptimizationSection(**obj)
        args = {"filtering": filtering_section, "nodal_optimization": nodal_optimization_section}
        return OptimizationProperties.model_validate(args)

    def _to_adequacy_patch(self) -> t.Optional[AdequacyPathProperties]:
        obj = {name: getattr(self, name) for name in AdequacyPathProperties.AdequacyPathSection.model_fields}
        # If all fields are `None`, the object is empty.
        if all(value is None for value in obj.values()):
            return None
        adequacy_path_section = AdequacyPathProperties.AdequacyPathSection(**obj)
        return AdequacyPathProperties.model_validate({"adequacy_patch": adequacy_path_section})

    @property
    def area_folder(self) -> AreaFolder:
        area_folder = AreaFolder(
            optimization=self._to_optimization(),
            adequacy_patch=self._to_adequacy_patch(),
            # UI properties are not configurable in Table Mode
        )
        return area_folder
