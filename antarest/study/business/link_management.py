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

from pydantic import BaseModel, model_validator
from starlette.exceptions import HTTPException

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
DEFAULT_COLOR = 112


class LinkInfoDTOBase(BaseModel):
    area1: str
    area2: str
    hurdles_cost: t.Optional[bool] = False
    loop_flow: t.Optional[bool] = False
    use_phase_shifter: t.Optional[bool] = False
    transmission_capacities: t.Optional[str] = TransmissionCapacity.ENABLED.value
    asset_type: t.Optional[str] = AssetType.AC.value
    display_comments: t.Optional[bool] = True
    colorr: t.Optional[int] = DEFAULT_COLOR
    colorb: t.Optional[int] = DEFAULT_COLOR
    colorg: t.Optional[int] = DEFAULT_COLOR
    link_width: t.Optional[float] = 1
    link_style: t.Optional[str] = LinkStyle.PLAIN.value


class LinkInfoDTO820(LinkInfoDTOBase):
    filter_synthesis: t.Optional[str] = None
    filter_year_by_year: t.Optional[str] = None


LinkInfoDTOType = t.Union[LinkInfoDTO820, LinkInfoDTOBase]


class LinkInfoFactory:
    @staticmethod
    def create_link_info(version: int, **kwargs: t.Any) -> LinkInfoDTOType:
        """
        Creates a LinkInfoDTO object corresponding to the specified version.

        Args:
            version (int): The study version.
            kwargs: The arguments passed for the DTO creation.

        Returns:
            LinkInfoDTOType: An object of type LinkInfoDTOBase or LinkInfoDTO820 depending on the version.
        """
        LinkInfoFactory._check_version_coherence(version, **kwargs)
        link_info = LinkInfoFactory._initialize_link_info(version, **kwargs)
        LinkInfoFactory._set_default_filters(version, link_info)

        return link_info

    @staticmethod
    def _initialize_link_info(version: int, **kwargs: t.Any) -> LinkInfoDTOType:
        """
        Initializes the LinkInfoDTO object based on the study version.

        Args:
            version (int): The study version.
            kwargs: The arguments passed for the DTO creation.

        Returns:
            LinkInfoDTOType: An object of type LinkInfoDTOBase or LinkInfoDTO820 depending on the version.
        """
        if version >= 820:
            return LinkInfoDTO820(**kwargs)
        return LinkInfoDTOBase(**kwargs)

    @staticmethod
    def _set_default_filters(version: int, link_info: LinkInfoDTOType) -> None:
        """
        Sets default filters if the study version is 820 or higher.

        Args:
            version (int): The study version.
            link_info (LinkInfoDTOType): The created DTO object.
        """
        if version >= 820 and isinstance(link_info, LinkInfoDTO820):
            if link_info.filter_synthesis is None:
                link_info.filter_synthesis = FilteringOptions.FILTER_SYNTHESIS
            if link_info.filter_year_by_year is None:
                link_info.filter_year_by_year = FilteringOptions.FILTER_YEAR_BY_YEAR

    @staticmethod
    def _check_version_coherence(version: int, **kwargs: t.Any) -> None:
        """
        Checks if filters are provided for a study version lower than 820.

        Args:
            version (int): The study version.
            kwargs: The arguments passed for the DTO creation.

        Raises:
            InvalidFieldForVersionError: If filters are provided for a version lower than 820.
        """
        if version < 820 and kwargs.get("_filters_provided"):
            raise InvalidFieldForVersionError(
                "Filters filter_synthesis and filter_year_by_year cannot be used for study versions lower than 820."
            )

    @staticmethod
    def create_parameters(
        study_version: int, link_creation_info: LinkInfoDTOType
    ) -> t.Dict[str, t.Union[str, bool, float, None]]:
        """
        Creates the parameters for the link creation command, handling version differences.

        Args:
            study_version (int): The study version.
            link_creation_info (LinkInfoDTOType): The link information for creation.

        Returns:
            t.Dict[str, t.Union[str, bool, float, None]: A dictionary containing the parameters for the command.
        """
        parameters = link_creation_info.model_dump(exclude={"area1", "area2"}, exclude_none=True)
        return parameters


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

                link_creation_data = {
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

                if with_ui:
                    link_creation_data.update(
                        {
                            "colorr": link_properties.get("colorr", DEFAULT_COLOR),
                            "colorb": link_properties.get("colorb", DEFAULT_COLOR),
                            "colorg": link_properties.get("colorg", DEFAULT_COLOR),
                            "link_width": link_properties.get("link-width", 1.0),
                            "link_style": link_properties.get("link-style", LinkStyle.PLAIN),
                        }
                    )
                else:
                    link_creation_data.update(
                        {
                            "colorr": None,
                            "colorb": None,
                            "colorg": None,
                            "link_width": None,
                            "link_style": None,
                        }
                    )

                link_info_dto = LinkInfoFactory.create_link_info(int(study.version), **link_creation_data)
                result.append(link_info_dto)

        return result

    def create_link(self, study: RawStudy, link_creation_info: LinkInfoDTOType) -> LinkInfoDTOType:
        study_version = int(study.version)

        link_info_dto_data = {
            "study_version": int(study.version),
            "area1": link_creation_info.area1,
            "area2": link_creation_info.area2,
            "hurdles_cost": link_creation_info.hurdles_cost,
            "loop_flow": link_creation_info.loop_flow,
            "use_phase_shifter": link_creation_info.use_phase_shifter,
            "transmission_capacities": link_creation_info.transmission_capacities,
            "asset_type": link_creation_info.asset_type,
            "display_comments": link_creation_info.display_comments,
            "colorr": link_creation_info.colorr,
            "colorb": link_creation_info.colorb,
            "colorg": link_creation_info.colorg,
            "link_width": link_creation_info.link_width,
            "link_style": link_creation_info.link_style,
        }

        if study_version >= 820 and isinstance(link_creation_info, LinkInfoDTO820):
            link_info_dto_data["filter_synthesis"] = link_creation_info.filter_synthesis
            link_info_dto_data["filter_year_by_year"] = link_creation_info.filter_year_by_year
        else:
            if isinstance(link_creation_info, LinkInfoDTO820) and (
                link_creation_info.filter_synthesis is not None or link_creation_info.filter_year_by_year is not None
            ):
                link_info_dto_data["_filters_provided"] = True

        link_info_dto = LinkInfoFactory.create_link_info(study_version, **link_info_dto_data)

        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)

        command = CreateLink(
            area1=link_creation_info.area1,
            area2=link_creation_info.area2,
            parameters=LinkInfoFactory.create_parameters(study_version, link_info_dto),
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
            updated_link_properties = old_link_dto.copy(
                update=update_link_dto.model_dump(by_alias=False, exclude_none=True)
            )
            new_links_by_ids[(area1, area2)] = updated_link_properties

            # Convert the DTO to a configuration object and update the configuration file.
            properties = LinkProperties(**updated_link_properties.model_dump(by_alias=False))
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
    def get_table_schema() -> JSON:
        return LinkOutput.schema()
