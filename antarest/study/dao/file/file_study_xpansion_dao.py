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
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import polars as pl
from typing_extensions import override

from antarest.core.exceptions import (
    AreaNotFound,
    CandidateNotFoundError,
    ChildNotFoundError,
    FileCurrentlyUsedInSettings,
    LinkNotFound,
    XpansionCandidateDeletionError,
    XpansionConfigurationAlreadyExists,
    XpansionConfigurationDoesNotExist,
    XpansionFileNotFoundError,
)
from antarest.study.business.model.xpansion_model import (
    XpansionAdequacyCriterion,
    XpansionCandidate,
    XpansionResourceFileType,
    XpansionSensitivitySettings,
    XpansionSettings,
    XpansionSettingsUpdate,
)
from antarest.study.dao.api.xpansion_dao import XpansionDao
from antarest.study.dao.common import XpansionCapacitiesMapping, XpansionConstraintsMapping, XpansionWeightsMapping
from antarest.study.storage.rawstudy.model.filesystem.config.xpansion import (
    parse_xpansion_adequacy_criterion,
    parse_xpansion_sensitivity_settings,
    parse_xpansion_settings,
    serialize_xpansion_adequacy_criterion,
    serialize_xpansion_sensitivity_settings,
    serialize_xpansion_settings,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


class FileStudyXpansionDao(XpansionDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_all_xpansion_candidates(self) -> list[XpansionCandidate]:
        candidates = self._get_all_xpansion_candidates()
        return [XpansionCandidate(**c) for c in candidates.values()]

    @override
    def get_xpansion_candidate(self, candidate_id: str) -> XpansionCandidate:
        # This takes the first candidate with the given name and not the id, because the name is the primary key.
        candidates = self._get_all_xpansion_candidates()
        try:
            candidate = next(c for c in candidates.values() if c["name"] == candidate_id)
            return XpansionCandidate(**candidate)

        except StopIteration:
            raise CandidateNotFoundError(f"The candidate '{candidate_id}' does not exist")

    @override
    def checks_xpansion_candidate_coherence(self, candidate: XpansionCandidate) -> None:
        self._assert_link_profile_are_files(candidate)
        self._assert_link_exist(candidate)

    @override
    def checks_xpansion_candidate_can_be_deleted(self, candidate_name: str) -> None:
        file_study = self.get_file_study()
        sensitivity_config = self._get_xpansion_sensitivity(file_study)
        projections = sensitivity_config.get("projection", {})
        if candidate_name in projections:
            raise XpansionCandidateDeletionError(file_study.config.study_id, candidate_name)

    @override
    def save_xpansion_candidate(self, candidate: XpansionCandidate, old_id: str | None = None) -> None:
        self._save_xpansion_candidates([(candidate, old_id)])

    def _save_xpansion_candidates(self, candidates: list[tuple[XpansionCandidate, str | None]]) -> None:
        existing_candidates = self._get_all_xpansion_candidates()
        existing_ids = {value["name"]: key for key, value in existing_candidates.items()}

        for candidate, old_id in candidates:
            if old_id:
                if old_id not in existing_ids:
                    raise CandidateNotFoundError(f"The candidate '{old_id}' does not exist")
                del existing_candidates[existing_ids[old_id]]

            new_key = existing_ids.get(
                candidate.name, str(len(existing_candidates) + 1)
            )  # The first candidate key is 1

            existing_candidates[new_key] = candidate.model_dump(mode="json", by_alias=True, exclude_none=True)

        self._save_candidates(existing_candidates)

    @override
    def save_xpansion_candidates(self, candidates: list[XpansionCandidate]) -> None:
        self._save_xpansion_candidates([(cdt, None) for cdt in candidates])

    @override
    def delete_xpansion_candidate(self, candidate_name: str) -> None:
        candidates = self._get_all_xpansion_candidates()
        existing_ids = {value["name"]: key for key, value in candidates.items()}
        if candidate_name not in existing_ids:
            raise CandidateNotFoundError(f"The candidate '{candidate_name}' does not exist")
        del candidates[existing_ids[candidate_name]]
        # Reorder keys of the dict
        new_dict = {str(i): v for i, (k, v) in enumerate(candidates.items(), 1)}
        self._save_candidates(new_dict)

    @override
    def get_xpansion_settings(self) -> XpansionSettings:
        file_study = self.get_file_study()
        try:
            settings = self._get_settings(file_study)
        except ChildNotFoundError:
            raise XpansionConfigurationDoesNotExist(file_study.config.study_id) from None
        sensitivity_settings = self._get_sensitivity_settings(file_study)
        settings.sensitivity_config = sensitivity_settings
        return settings

    @override
    def save_xpansion_settings(self, settings: XpansionSettings) -> None:
        file_study = self.get_file_study()

        sensitivity_content = serialize_xpansion_sensitivity_settings(settings.sensitivity_config)
        file_study.tree.save(sensitivity_content, ["user", "expansion", "sensitivity", "sensitivity_in"])

        settings_content = serialize_xpansion_settings(settings)
        file_study.tree.save(settings_content, ["user", "expansion", "settings"])

    @override
    def checks_xpansion_settings_are_correct(self, settings: XpansionSettingsUpdate) -> None:
        """
        Checks yearly_weights and additional_constraints fields.
        - If the attributes are given, it means that the user wants to select a file.
          It is therefore necessary to check that the file exists.
        """
        file_study = self.get_file_study()
        for field in ["additional_constraints", "yearly_weights"]:
            if file := getattr(settings, field, None):
                file_type = field.split("_")[1]
                try:
                    file_url = ["user", "expansion", file_type, file]
                    file_study.tree.get_node(file_url)
                except ChildNotFoundError:
                    msg = f"Additional {file_type} file '{file}' does not exist"
                    raise XpansionFileNotFoundError(msg) from None

    @override
    def get_xpansion_resource(self, resource_type: XpansionResourceFileType, filename: str) -> bytes | pl.DataFrame:
        file_study = self.get_file_study()
        try:
            node = file_study.tree.get_node(self.get_resource_dir(resource_type) + [filename])
        except ChildNotFoundError:
            raise XpansionFileNotFoundError(f"The '{resource_type.value}' file '{filename}' does not exist") from None

        if isinstance(node, MatrixNode):
            return node.parse_as_dataframe()

        content = node.get()
        assert isinstance(content, bytes)
        return content

    @override
    def get_xpansion_resources(self, resource_type: XpansionResourceFileType) -> list[str]:
        file_study = self.get_file_study()
        try:
            folder_path = self.get_resource_dir(resource_type)
            return sorted(file_study.tree.get(folder_path).keys())
        except ChildNotFoundError:
            return []

    @override
    def checks_xpansion_resource_can_be_deleted(self, resource_type: XpansionResourceFileType, filename: str) -> None:
        file_checkers = {
            XpansionResourceFileType.CONSTRAINTS: self._is_constraints_file_used,
            XpansionResourceFileType.CAPACITIES: self._is_capa_file_used,
            XpansionResourceFileType.WEIGHTS: self._is_weights_file_used,
        }

        if resource_type in file_checkers and file_checkers[resource_type](filename):
            raise FileCurrentlyUsedInSettings(resource_type, filename)

    @override
    def get_xpansion_adequacy_criterion(self) -> XpansionAdequacyCriterion:
        file_study = self.get_file_study()
        try:
            content = file_study.tree.get(["user", "expansion", "adequacy_criterion", "adequacy_criterion"])
            return parse_xpansion_adequacy_criterion(content)
        except ChildNotFoundError:
            return XpansionAdequacyCriterion()

    @override
    def create_xpansion_configuration(self) -> None:
        file_study = self.get_file_study()
        try:
            file_study.tree.get(["user", "expansion"])
        except ChildNotFoundError:
            # We want to create the folder, so we expect this exception.
            xpansion_configuration_data = {
                "user": {
                    "expansion": {
                        "settings": serialize_xpansion_settings(XpansionSettings()),
                        "sensitivity": {"sensitivity_in": {}},
                        "candidates": {},
                        "capa": {},
                        "weights": {},
                        "constraints": {},
                        "adequacy_criterion": {"adequacy_criterion": {}},
                    }
                }
            }

            file_study.tree.save(xpansion_configuration_data)
        else:
            raise XpansionConfigurationAlreadyExists(file_study.config.study_id)

    @override
    def delete_xpansion_configuration(self) -> None:
        file_study = self.get_file_study()
        try:
            file_study.tree.delete(["user", "expansion"])
        except ChildNotFoundError:
            raise XpansionConfigurationDoesNotExist(file_study.config.study_id)

    @override
    def delete_xpansion_resource(self, resource_type: XpansionResourceFileType, filename: str) -> None:
        file_study = self.get_file_study()
        try:
            file_study.tree.delete(self.get_resource_dir(resource_type) + [filename])
        except ChildNotFoundError:
            raise XpansionFileNotFoundError(f"The '{resource_type.value}' file '{filename}' does not exist") from None

    @override
    def save_xpansion_constraint(self, data: XpansionConstraintsMapping) -> None:
        for filename, content in data.items():
            self.save_resource(XpansionResourceFileType.CONSTRAINTS, filename, content)

    @override
    def save_xpansion_capacity(self, data: XpansionCapacitiesMapping) -> None:
        for filename, series_id in data.items():
            self.save_resource(XpansionResourceFileType.CAPACITIES, filename, series_id)

    @override
    def save_xpansion_weight(self, data: XpansionWeightsMapping) -> None:
        for filename, series_id in data.items():
            self.save_resource(XpansionResourceFileType.WEIGHTS, filename, series_id)

    @override
    def save_xpansion_adequacy_criterion(self, criterion: XpansionAdequacyCriterion) -> None:
        # Checks if the provided areas exist in the study
        file_study = self.get_file_study()
        missing_areas = ""
        for pattern in criterion.patterns:
            if pattern.area not in file_study.config.areas:
                missing_areas += pattern.area
        if missing_areas:
            raise AreaNotFound(missing_areas)
        # Save the data inside the file
        content = serialize_xpansion_adequacy_criterion(criterion)
        file_study.tree.save(data=content, url=["user", "expansion", "adequacy_criterion", "adequacy_criterion"])

    def _get_all_resources(self, url: list[str]) -> dict[str, str]:
        file_study = self.get_file_study()
        try:
            folder_node = file_study.tree.get_node(url)
        except ChildNotFoundError:
            return {}
        node_mapping = {}
        for file_name in folder_node.get():
            node = folder_node.get_node([file_name])
            assert isinstance(node, MatrixNode)
            node_mapping[node] = file_name

        result = {}

        matrices_mapping = self.get_impl().get_matrices_ids(list(node_mapping))
        for node, matrix_id in matrices_mapping.items():
            result[node_mapping[node]] = matrix_id

        return result

    @override
    def get_all_xpansion_weights(self) -> XpansionWeightsMapping:
        url = self.get_resource_dir(XpansionResourceFileType.WEIGHTS)
        return self._get_all_resources(url)

    @override
    def get_all_xpansion_capacities(self) -> XpansionCapacitiesMapping:
        url = self.get_resource_dir(XpansionResourceFileType.CAPACITIES)
        return self._get_all_resources(url)

    @override
    def get_all_xpansion_constraints(self) -> XpansionConstraintsMapping:
        file_study = self.get_file_study()
        try:
            folder_node = file_study.tree.get_node(self.get_resource_dir(XpansionResourceFileType.CONSTRAINTS))
        except ChildNotFoundError:
            return {}

        result: XpansionConstraintsMapping = {}
        for file_name in folder_node.get():
            content = folder_node.get([file_name])
            assert isinstance(content, bytes)
            result[file_name] = content

        return result

    def save_resource(self, resource_type: XpansionResourceFileType, filename: str, data: bytes | str) -> None:
        file_study = self.get_file_study()
        url = self.get_resource_dir(resource_type)
        file_study.tree.save(data=data, url=url + [filename])

    @staticmethod
    def _get_sensitivity_settings(file_study: FileStudy) -> XpansionSensitivitySettings:
        try:
            args = file_study.tree.get(["user", "expansion", "sensitivity", "sensitivity_in"])
            return parse_xpansion_sensitivity_settings(args)
        except ChildNotFoundError:
            return XpansionSensitivitySettings()

    @staticmethod
    def _get_settings(file_study: FileStudy) -> XpansionSettings:
        config_obj = file_study.tree.get(["user", "expansion", "settings"])
        return parse_xpansion_settings(config_obj)

    def _save_candidates(self, content: dict[str, Any]) -> None:
        self.get_file_study().tree.save(content, ["user", "expansion", "candidates"])

    def _get_all_xpansion_candidates(self) -> dict[str, Any]:
        file_study = self.get_file_study()
        return file_study.tree.get(["user", "expansion", "candidates"])

    def _assert_link_profile_are_files(self, xpansion_candidate_dto: XpansionCandidate) -> None:
        file_study = self.get_file_study()
        existing_files = file_study.tree.get(["user", "expansion", "capa"])
        for attr in [
            "link_profile",
            "already_installed_link_profile",
            "direct_link_profile",
            "indirect_link_profile",
            "already_installed_direct_link_profile",
            "already_installed_indirect_link_profile",
        ]:
            if link_file := getattr(xpansion_candidate_dto, attr, None):
                if link_file not in existing_files:
                    raise XpansionFileNotFoundError(f"The '{attr}' file '{link_file}' does not exist")

    def _assert_link_exist(self, xpansion_candidate_dto: XpansionCandidate) -> None:
        file_study = self.get_file_study()
        area_from = xpansion_candidate_dto.link.area_from
        area_to = xpansion_candidate_dto.link.area_to
        if area_from not in file_study.config.areas:
            raise AreaNotFound(area_from)
        if area_to not in file_study.config.get_links(area_from):
            raise LinkNotFound(f"The link from '{area_from}' to '{area_to}' not found")

    @staticmethod
    def _get_xpansion_sensitivity(file_study: FileStudy) -> dict[str, Any]:
        try:
            return file_study.tree.get(["user", "expansion", "sensitivity", "sensitivity_in"])
        except ChildNotFoundError:
            return {}

    @staticmethod
    def get_resource_dir(resource_type: XpansionResourceFileType) -> list[str]:
        if resource_type == XpansionResourceFileType.CONSTRAINTS:
            return ["user", "expansion", "constraints"]
        elif resource_type == XpansionResourceFileType.CAPACITIES:
            return ["user", "expansion", "capa"]
        elif resource_type == XpansionResourceFileType.WEIGHTS:
            return ["user", "expansion", "weights"]
        raise NotImplementedError(f"resource_type '{resource_type}' not implemented")

    def _is_constraints_file_used(self, filename: str) -> bool:
        settings = self._get_settings(self.get_file_study())
        if settings.additional_constraints == filename:
            return True
        return False

    def _is_weights_file_used(self, filename: str) -> bool:
        settings = self._get_settings(self.get_file_study())
        if settings.yearly_weights == filename:
            return True
        return False

    def _is_capa_file_used(self, filename: str) -> bool:
        candidates = self.get_all_xpansion_candidates()
        for candidate in candidates:
            if candidate.link_profile == filename:
                return True
            if candidate.already_installed_link_profile == filename:
                return True
            if candidate.direct_link_profile == filename:
                return True
            if candidate.indirect_link_profile == filename:
                return True
            if candidate.already_installed_direct_link_profile == filename:
                return True
            if candidate.already_installed_indirect_link_profile == filename:
                return True
        return False
