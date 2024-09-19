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

import typing as t

from pydantic import BaseModel

from antarest.core.exceptions import ConfigFileNotFound, InvalidFieldForVersionError
from antarest.core.model import JSON
from antarest.study.business.all_optional_meta import all_optional_model, camel_case_model
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import RawStudy
from antarest.study.storage.rawstudy.model.filesystem.config.links import (
    AssetType,
    LinkProperties,
    LinkStyle,
    TransmissionCapacity,
)
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.common import FilteringOptions
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.remove_link import RemoveLink
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig

_ALL_LINKS_PATH = "input/links"
DEFAULT_COLOR = "112"


class LinkInfoDTOBase(BaseModel):
    area1: str
    area2: str
    hurdles_cost: t.Optional[bool] = False
    loop_flow: t.Optional[bool] = False
    use_phase_shifter: t.Optional[bool] = False
    transmission_capacities: t.Optional[str] = TransmissionCapacity.ENABLED
    asset_type: t.Optional[str] = AssetType.AC
    display_comments: t.Optional[bool] = True
    colorr: t.Optional[str] = DEFAULT_COLOR
    colorb: t.Optional[str] = DEFAULT_COLOR
    colorg: t.Optional[str] = DEFAULT_COLOR
    link_width: t.Optional[float] = 1
    link_style: t.Optional[str] = LinkStyle.PLAIN


class LinkInfoDTO820(LinkInfoDTOBase):
    filter_synthesis: t.Optional[str] = None
    filter_year_by_year: t.Optional[str] = None


LinkInfoDTOType = t.Union[LinkInfoDTO820, LinkInfoDTOBase]


class LinkInfoFactory:
    @staticmethod
    def create_link_info(**kwargs) -> LinkInfoDTOType:
        filters_provided = kwargs.get("filter_synthesis") is not None or kwargs.get("filter_year_by_year") is not None

        if kwargs.get("version") >= 820:
            link_info = LinkInfoDTO820(**kwargs)
            if link_info.filter_synthesis is None:
                link_info.filter_synthesis = FilteringOptions.FILTER_SYNTHESIS
            if link_info.filter_year_by_year is None:
                link_info.filter_year_by_year = FilteringOptions.FILTER_YEAR_BY_YEAR
        else:
            link_info = LinkInfoDTOBase(**kwargs)

        link_info._filters_provided = filters_provided
        return link_info


@all_optional_model
@camel_case_model
class LinkOutput(LinkProperties):
    """
    DTO object use to get the link information.
    """


class LinkManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_all_links(self, study: RawStudy, with_ui: bool = False) -> t.List[LinkInfoDTOType]:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        result = []
        for area_id, area in file_study.config.areas.items():
            links_config = file_study.tree.get(["input", "links", area_id, "properties"])
            for link in area.links:
                link_properties = links_config[link]
                link_info_args = {
                    "version": int(study.version),
                    "area1": area_id,
                    "area2": link,
                    "hurdles_cost": link_properties.get("hurdles-cost"),
                    "loop_flow": link_properties.get("loop-flow"),
                    "use_phase_shifter": link_properties.get("use-phase-shifter"),
                    "transmission_capacities": link_properties.get("transmission-capacities"),
                    "asset_type": link_properties.get("asset-type"),
                    "display_comments": link_properties.get("display-comments"),
                    "filter_synthesis": link_properties.get("filter-synthesis"),
                    "filter_year_by_year": link_properties.get("filter-year-by-year"),
                }
                if with_ui and links_config and link in links_config:
                    link_info_args.update(
                        {
                            "colorr": str(link_properties.get("colorr", "112")),
                            "colorb": str(link_properties.get("colorb", "112")),
                            "colorg": str(link_properties.get("colorg", "112")),
                            "link_width": link_properties.get("link-width", 1.0),
                            "link_style": link_properties.get("link-style", "plain"),
                        }
                    )
                else:
                    link_info_args.update(
                        {"colorr": None, "colorb": None, "colorg": None, "link_width": None, "link_style": None}
                    )
                link_info_dto = LinkInfoFactory.create_link_info(**link_info_args)

                result.append(link_info_dto)
        return result

    def create_link(self, study: RawStudy, link_creation_info: LinkInfoDTOType) -> LinkInfoDTOType:
        study_version = int(study.version)
        link_info_dto = LinkInfoFactory.create_link_info(
            version=int(study.version),
            area1=link_creation_info.area1,
            area2=link_creation_info.area2,
            hurdles_cost=link_creation_info.hurdles_cost,
            loop_flow=link_creation_info.loop_flow,
            use_phase_shifter=link_creation_info.use_phase_shifter,
            transmission_capacities=link_creation_info.transmission_capacities,
            asset_type=link_creation_info.asset_type,
            display_comments=link_creation_info.display_comments,
            colorr=link_creation_info.colorr,
            colorb=link_creation_info.colorb,
            colorg=link_creation_info.colorg,
            link_width=link_creation_info.link_width,
            link_style=link_creation_info.link_style,
            filter_synthesis=link_creation_info.filter_synthesis if study_version >= 820 else None,
            filter_year_by_year=link_creation_info.filter_year_by_year if study_version >= 820 else None,
        )
        self.check_version_coherence(study_version, link_info_dto)

        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)

        command = CreateLink(
            area1=link_creation_info.area1,
            area2=link_creation_info.area2,
            parameters=self.create_parameters(int(study.version), link_info_dto),
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )

        execute_or_add_commands(study, file_study, [command], self.storage_service)

        return link_info_dto

    def delete_link(self, study: RawStudy, area1_id: str, area2_id: str) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        command = RemoveLink(
            area1=area1_id,
            area2=area2_id,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    def get_all_links_props(self, study: RawStudy) -> t.Mapping[t.Tuple[str, str], LinkOutput]:
        """
        Retrieves all links properties from the study.

        Args:
            study: The raw study object.
        Returns:
            A mapping of link IDS `(area1_id, area2_id)` to link properties.
        Raises:
            ConfigFileNotFound: if a configuration file is not found.
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)

        # Get the link information from the `input/links/{area1}/properties.ini` file.
        path = _ALL_LINKS_PATH
        try:
            links_cfg = file_study.tree.get(path.split("/"), depth=5)
        except KeyError:
            raise ConfigFileNotFound(path) from None

        # areas_cfg contains a dictionary where the keys are the area IDs,
        # and the values are objects that can be converted to `LinkFolder`.
        links_by_ids = {}
        for area1_id, entries in links_cfg.items():
            property_map = entries.get("properties") or {}
            for area2_id, properties_cfg in property_map.items():
                area1_id, area2_id = sorted([area1_id, area2_id])
                properties = LinkProperties(**properties_cfg)
                links_by_ids[(area1_id, area2_id)] = LinkOutput(**properties.model_dump(by_alias=False))

        return links_by_ids

    def update_links_props(
        self,
        study: RawStudy,
        update_links_by_ids: t.Mapping[t.Tuple[str, str], LinkOutput],
    ) -> t.Mapping[t.Tuple[str, str], LinkOutput]:
        old_links_by_ids = self.get_all_links_props(study)
        new_links_by_ids = {}
        file_study = self.storage_service.get_storage(study).get_raw(study)
        commands = []
        for (area1, area2), update_link_dto in update_links_by_ids.items():
            # Update the link properties.
            old_link_dto = old_links_by_ids[(area1, area2)]
            new_link_dto = old_link_dto.copy(update=update_link_dto.model_dump(by_alias=False, exclude_none=True))
            new_links_by_ids[(area1, area2)] = new_link_dto

            # Convert the DTO to a configuration object and update the configuration file.
            properties = LinkProperties(**new_link_dto.model_dump(by_alias=False))
            path = f"{_ALL_LINKS_PATH}/{area1}/properties/{area2}"
            cmd = UpdateConfig(
                target=path,
                data=properties.to_config(),
                command_context=self.storage_service.variant_study_service.command_factory.command_context,
            )
            commands.append(cmd)

        execute_or_add_commands(study, file_study, commands, self.storage_service)
        return new_links_by_ids

    @staticmethod
    def check_version_coherence(study_version: int, link_creation_info: LinkInfoDTOType) -> None:
        if study_version < 820:
            if getattr(link_creation_info, "_filters_provided", True):
                raise InvalidFieldForVersionError(
                    f"You cannot specify a filter synthesis or filter year by year as your study version is earlier than v8.2"
                )

    @staticmethod
    def get_table_schema() -> JSON:
        return LinkOutput.schema()

    @staticmethod
    def create_parameters(study_version: int, link_creation_info: LinkInfoDTOType) -> t.Dict[str, str]:
        parameters = {
            "hurdles-cost": link_creation_info.hurdles_cost,
            "loop-flow": link_creation_info.loop_flow,
            "use-phase-shifter": link_creation_info.use_phase_shifter,
            "transmission-capacities": link_creation_info.transmission_capacities,
            "asset-type": link_creation_info.asset_type,
            "display-comments": link_creation_info.display_comments,
            "colorr": link_creation_info.colorr,
            "colorb": link_creation_info.colorb,
            "colorg": link_creation_info.colorg,
            "link-width": link_creation_info.link_width,
            "link-style": link_creation_info.link_style,
        }

        if study_version >= 820 and isinstance(link_creation_info, LinkInfoDTO820):
            parameters["filter-synthesis"] = link_creation_info.filter_synthesis
            parameters["filter-year-by-year"] = link_creation_info.filter_year_by_year

        return parameters
