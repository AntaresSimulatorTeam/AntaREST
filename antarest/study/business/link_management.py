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

import typing as t
from typing import Any

from antares.study.version import StudyVersion

from antarest.core.exceptions import LinkNotFound
from antarest.core.model import JSON
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.business.model.link_model import LinkBaseDTO, LinkDTO, LinkInternal, LinkTsGeneration
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import LinksParametersTsGeneration, RawStudy, Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.remove_link import RemoveLink
from antarest.study.storage.variantstudy.model.command.update_link import UpdateLink


class LinkManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_all_links(self, study: Study) -> t.List[LinkDTO]:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        result: t.List[LinkDTO] = []

        ts_generation_parameters = self.get_all_links_ts_generation_information(study.id)

        for area_id, area in file_study.config.areas.items():
            links_config = file_study.tree.get(["input", "links", area_id, "properties"])

            for link in area.links:
                link_tree_config: t.Dict[str, t.Any] = links_config[link]
                link_tree_config.update({"area1": area_id, "area2": link})

                if area_id in ts_generation_parameters and link in ts_generation_parameters[area_id]:
                    link_ts_generation = ts_generation_parameters[area_id][link]
                    link_tree_config.update(link_ts_generation.model_dump(mode="json"))

                link_internal = LinkInternal.model_validate(link_tree_config)

                result.append(link_internal.to_dto())

        return result

    def get_link(self, study: RawStudy, link: LinkInternal) -> LinkInternal:
        file_study = self.storage_service.get_storage(study).get_raw(study)

        link_properties = self._get_link_if_exists(file_study, link)

        link_properties.update({"area1": link.area1, "area2": link.area2})

        ts_generation_parameters = self.get_single_link_ts_generation_information(study.id, link.area1, link.area2)
        link_properties.update(ts_generation_parameters.model_dump(mode="json"))

        updated_link = LinkInternal.model_validate(link_properties)

        return updated_link

    @staticmethod
    def get_all_links_ts_generation_information(study_id: str) -> t.Dict[str, t.Dict[str, LinkTsGeneration]]:
        db_dictionnary: t.Dict[str, t.Dict[str, LinkTsGeneration]] = {}
        with db():
            all_links_parameters: t.List[LinksParametersTsGeneration] = (
                db.session.query(LinksParametersTsGeneration).filter_by(study_id=study_id).all()
            )
            for link_parameters in all_links_parameters:
                area_from = link_parameters.area_from
                area_to = link_parameters.area_to
                db_dictionnary.setdefault(area_from, {})[area_to] = LinkTsGeneration.from_db_model(link_parameters)
        return db_dictionnary

    @staticmethod
    def get_single_link_ts_generation_information(study_id: str, area_from: str, area_to: str) -> LinkTsGeneration:
        with db():
            links_parameters = (
                db.session.query(LinksParametersTsGeneration)
                .filter_by(study_id=study_id, area_from=area_from, area_to=area_to)
                .first()
            )
            if links_parameters:
                return LinkTsGeneration.from_db_model(links_parameters)
        return LinkTsGeneration()

    def create_link(self, study: Study, link_creation_dto: LinkDTO) -> LinkDTO:
        link = link_creation_dto.to_internal(StudyVersion.parse(study.version))

        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)

        command = CreateLink(
            area1=link.area1,
            area2=link.area2,
            parameters=link.model_dump(exclude_none=True),
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
            study_version=file_study.config.version,
        )

        execute_or_add_commands(study, file_study, [command], self.storage_service)

        return link_creation_dto

    def update_link(self, study: RawStudy, area_from: str, area_to: str, link_update_dto: LinkBaseDTO) -> LinkDTO:
        link_dto = LinkDTO(area1=area_from, area2=area_to, **link_update_dto.model_dump(exclude_unset=True))

        link = link_dto.to_internal(StudyVersion.parse(study.version))
        file_study = self.storage_service.get_storage(study).get_raw(study)

        self._get_link_if_exists(file_study, link)

        command = UpdateLink(
            area1=link.area1,
            area2=link.area2,
            parameters=link.model_dump(
                include=link_update_dto.model_fields_set, exclude={"area1", "area2"}, exclude_none=True
            ),
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
            study_version=file_study.config.version,
        )

        execute_or_add_commands(study, file_study, [command], self.storage_service)

        updated_link = self.get_link(study, link)

        return updated_link.to_dto()

    def update_links(
        self,
        study: RawStudy,
        update_links_by_ids: t.Mapping[t.Tuple[str, str], LinkBaseDTO],
    ) -> t.Mapping[t.Tuple[str, str], LinkBaseDTO]:
        new_links_by_ids = {}
        for (area1, area2), update_link_dto in update_links_by_ids.items():
            updated_link = self.update_link(study, area1, area2, update_link_dto)
            new_links_by_ids[(area1, area2)] = updated_link

        return new_links_by_ids

    def delete_link(self, study: RawStudy, area1_id: str, area2_id: str) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        command = RemoveLink(
            area1=area1_id,
            area2=area2_id,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
            study_version=file_study.config.version,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    def _get_link_if_exists(self, file_study: FileStudy, link: LinkInternal) -> dict[str, Any]:
        try:
            return file_study.tree.get(["input", "links", link.area1, "properties", link.area2])
        except KeyError:
            raise LinkNotFound(f"The link {link.area1} -> {link.area2} is not present in the study")

    @staticmethod
    def get_table_schema() -> JSON:
        return LinkBaseDTO.model_json_schema()
