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
import operator
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING

import polars as pl
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, ChildNotFoundError, STStorageConfigNotFound, STStorageNotFound
from antarest.study.business.model.sts_model import (
    STStorage,
    STStorageAdditionalConstraint,
    STStorageAdditionalConstraintsMap,
)
from antarest.study.dao.api.st_storage_dao import STStorageDao
from antarest.study.dao.common import AreaId, StStorageId
from antarest.study.model import STUDY_VERSION_9_2
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import (
    parse_st_storage,
    parse_st_storage_additional_constraint,
    serialize_st_storage,
    serialize_st_storage_additional_constraint,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao

_STORAGE_LIST_PATH = "input/st-storage/clusters/{area_id}/list/{storage_id}"
_ALL_STORAGE_PATH = "input/st-storage/clusters"


class FileStudySTStorageDao(STStorageDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_all_st_storages(self) -> dict[str, dict[str, STStorage]]:
        study_data = self.get_file_study()
        path = _ALL_STORAGE_PATH
        try:
            # may raise KeyError if the path is missing
            storages = study_data.tree.get(path.split("/"), depth=5)
            # may raise KeyError if "list" is missing
            storages = {area_id: cluster_list["list"] for area_id, cluster_list in storages.items()}
        except KeyError:
            raise STStorageConfigNotFound(path) from None

        storages_by_areas: dict[str, dict[str, STStorage]] = {}
        for area_id, cluster_obj in storages.items():
            for cluster_id, cluster in cluster_obj.items():
                storage = parse_st_storage(study_data.config.version, cluster)
                storages_by_areas.setdefault(area_id, {})[storage.id] = storage

        return storages_by_areas

    @override
    def get_all_st_storages_for_area(self, area_id: str) -> Sequence[STStorage]:
        study_data = self.get_file_study()
        all_storages = self._get_all_storages_for_area(study_data, area_id)

        # Sort STStorage by groups and then by name
        order_by = operator.attrgetter("group", "name")
        return sorted(all_storages.values(), key=order_by)

    @override
    def get_st_storage(self, area_id: str, storage_id: str) -> STStorage:
        study_data = self.get_file_study()
        path = _STORAGE_LIST_PATH.format(area_id=area_id, storage_id=storage_id)
        try:
            config = study_data.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise STStorageNotFound(area_id, storage_id) from None
        return parse_st_storage(study_data.config.version, config)

    @override
    def st_storage_exists(self, area_id: str, storage_id: str) -> bool:
        file_study = self.get_file_study()
        path = _STORAGE_LIST_PATH.format(area_id=area_id, storage_id=storage_id)
        try:
            file_study.tree.get(path.split("/"), depth=1)
            return True
        except (KeyError, ChildNotFoundError):
            return False

    @override
    def get_st_storage_pmax_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self.get_impl().get_matrix(["input", "st-storage", "series", area_id, storage_id, "pmax_injection"])

    @override
    def get_st_storage_pmax_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self.get_impl().get_matrix(["input", "st-storage", "series", area_id, storage_id, "pmax_withdrawal"])

    @override
    def get_st_storage_lower_rule_curve(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self.get_impl().get_matrix(["input", "st-storage", "series", area_id, storage_id, "lower_rule_curve"])

    @override
    def get_st_storage_upper_rule_curve(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self.get_impl().get_matrix(["input", "st-storage", "series", area_id, storage_id, "upper_rule_curve"])

    @override
    def get_st_storage_inflows(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self.get_impl().get_matrix(["input", "st-storage", "series", area_id, storage_id, "inflows"])

    @override
    def get_st_storage_cost_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self.get_impl().get_matrix(["input", "st-storage", "series", area_id, storage_id, "cost_injection"])

    @override
    def get_st_storage_cost_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self.get_impl().get_matrix(["input", "st-storage", "series", area_id, storage_id, "cost_withdrawal"])

    @override
    def get_st_storage_cost_level(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self.get_impl().get_matrix(["input", "st-storage", "series", area_id, storage_id, "cost_level"])

    @override
    def get_st_storage_cost_variation_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        url = ["input", "st-storage", "series", area_id, storage_id, "cost_variation_injection"]
        return self.get_impl().get_matrix(url)

    @override
    def get_st_storage_cost_variation_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        url = ["input", "st-storage", "series", area_id, storage_id, "cost_variation_withdrawal"]
        return self.get_impl().get_matrix(url)

    @override
    def save_st_storages(self, data: dict[AreaId, list[STStorage]]) -> None:
        study_data = self.get_file_study()

        # Hold everything in memory to validate the data before saving it.
        url_content_pairs = []

        for area_id, storages in data.items():
            all_storages = self._get_all_storages_for_area(study_data, area_id)
            for st_storage in storages:
                self._update_st_storage_config(area_id, st_storage)
                all_storages[st_storage.id] = st_storage

            ini_content = {id: serialize_st_storage(study_data.config.version, sts) for id, sts in all_storages.items()}
            url_content_pairs.append((["input", "st-storage", "clusters", area_id, "list"], ini_content))

        # Now we save everything in the files
        for url, content in url_content_pairs:
            study_data.tree.save(content, url)

    @override
    def save_st_storage_pmax_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "st-storage", "series", area_id, storage_id, "pmax_injection"])

    @override
    def save_st_storage_pmax_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "st-storage", "series", area_id, storage_id, "pmax_withdrawal"])

    @override
    def save_st_storage_lower_rule_curve(self, area_id: str, storage_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "st-storage", "series", area_id, storage_id, "lower_rule_curve"])

    @override
    def save_st_storage_upper_rule_curve(self, area_id: str, storage_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "st-storage", "series", area_id, storage_id, "upper_rule_curve"])

    @override
    def save_st_storage_inflows(self, area_id: str, storage_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "st-storage", "series", area_id, storage_id, "inflows"])

    @override
    def save_st_storage_cost_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "st-storage", "series", area_id, storage_id, "cost_injection"])

    @override
    def save_st_storage_cost_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "st-storage", "series", area_id, storage_id, "cost_withdrawal"])

    @override
    def save_st_storage_cost_level(self, area_id: str, storage_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "st-storage", "series", area_id, storage_id, "cost_level"])

    @override
    def save_st_storage_cost_variation_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(
            series_id, ["input", "st-storage", "series", area_id, storage_id, "cost_variation_injection"]
        )

    @override
    def save_st_storage_cost_variation_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(
            series_id, ["input", "st-storage", "series", area_id, storage_id, "cost_variation_withdrawal"]
        )

    @override
    def delete_st_storage(self, area_id: str, storage: STStorage) -> None:
        study_data = self.get_file_study()
        storage_id = storage.id
        paths = [
            ["input", "st-storage", "clusters", area_id, "list", storage_id],
            ["input", "st-storage", "series", area_id, storage_id],
        ]
        if study_data.config.version >= STUDY_VERSION_9_2:
            if study_data.config.areas[area_id].st_storages_additional_constraints.get(storage_id):
                paths.append(["input", "st-storage", "constraints", area_id, storage_id])

        if len(study_data.config.areas[area_id].st_storages) == 1:
            paths.append(["input", "st-storage", "series", area_id])

        for path in paths:
            study_data.tree.delete(path)

        self._remove_st_storage_from_scenario_builder(area_id, storage_id)

        # Deleting the short-term storage in the configuration must be done AFTER deleting the files and folders.
        study_data.config.areas[area_id].st_storages.remove(storage)
        if study_data.config.version >= STUDY_VERSION_9_2:
            study_data.config.areas[area_id].st_storages_additional_constraints.pop(storage_id, None)

    @override
    def get_all_st_storage_additional_constraints(self) -> STStorageAdditionalConstraintsMap:
        file_study = self.get_file_study()
        path = ["input", "st-storage", "constraints"]
        try:
            all_constraints: STStorageAdditionalConstraintsMap = {}
            areas = file_study.tree.get(path, depth=2)
            for area, storages in areas.items():
                for storage in storages:
                    constraints = self.get_st_storage_additional_constraints(area, storage)
                    all_constraints.setdefault(area, {})[storage] = constraints
            return all_constraints
        except ChildNotFoundError:
            return {}

    @override
    def get_st_storage_additional_constraints(
        self, area_id: str, storage_id: str
    ) -> list[STStorageAdditionalConstraint]:
        file_study = self.get_file_study()
        path = ["input", "st-storage", "constraints", area_id, storage_id, "additional_constraints"]
        try:
            constraints: list[STStorageAdditionalConstraint] = []
            ini_content = file_study.tree.get(path)
            for key, value in ini_content.items():
                constraint = parse_st_storage_additional_constraint(key, value)
                constraints.append(constraint)
            return constraints
        except ChildNotFoundError:
            return []

    @override
    def save_st_storage_constraint_matrix(
        self, area_id: str, storage_id: str, constraint_id: str, series_id: str
    ) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(
            series_id, ["input", "st-storage", "constraints", area_id, storage_id, f"rhs_{constraint_id}"]
        )

    @override
    def get_st_storage_additional_constraint_matrix(
        self, area_id: str, storage_id: str, constraint_id: str
    ) -> pl.DataFrame:
        url = ["input", "st-storage", "constraints", area_id, storage_id, f"rhs_{constraint_id}"]
        return self.get_impl().get_matrix(url)

    @override
    def delete_st_storage_additional_constraints(self, area_id: str, storage_id: str, constraints: list[str]) -> None:
        study_data = self.get_file_study()
        for constraint in constraints:
            paths = [
                ["input", "st-storage", "constraints", area_id, storage_id, f"rhs_{constraint}"],
                ["input", "st-storage", "constraints", area_id, storage_id, "additional_constraints", constraint],
            ]
            for path in paths:
                study_data.tree.delete(path)

        self._remove_st_storage_constraints_from_scenario_builder(area_id, storage_id, set(constraints))

        # Deleting the constraints in the configuration must be done AFTER deleting the files and folders.
        existing_ids = {
            c.id: c for c in study_data.config.areas[area_id].st_storages_additional_constraints[storage_id]
        }
        for constraint in constraints:
            study_data.config.areas[area_id].st_storages_additional_constraints[storage_id].remove(
                existing_ids[constraint]
            )

    @override
    def save_st_storage_additional_constraints(
        self, data: dict[AreaId, dict[StStorageId, list[STStorageAdditionalConstraint]]]
    ) -> None:
        study_data = self.get_file_study()

        # Hold everything in memory to validate the data before saving it.
        url_content_pairs = []

        for area_id, value in data.items():
            for storage_id, constraints in value.items():
                existing_constraints = self.get_st_storage_additional_constraints(area_id, storage_id)

                existing_map = {c.id: c for c in existing_constraints}
                existing_map.update({c.id: c for c in constraints})

                ini_content = {}
                for constraint_id, constraint in existing_map.items():
                    ini_content[constraint.name] = serialize_st_storage_additional_constraint(constraint)

                # Save into the config
                self._update_st_storage_additional_constraints_config(area_id, storage_id, constraints)

                # We have to create the folder before saving the files
                (study_data.config.study_path / "input" / "st-storage" / "constraints" / area_id / storage_id).mkdir(
                    parents=True, exist_ok=True
                )
                url = ["input", "st-storage", "constraints", area_id, storage_id, "additional_constraints"]
                url_content_pairs.append((url, ini_content))

        # Save into the files
        for url, content in url_content_pairs:
            study_data.tree.save(content, url)

    @staticmethod
    def _get_all_storages_for_area(file_study: FileStudy, area_id: str) -> dict[str, STStorage]:
        path = _STORAGE_LIST_PATH.format(area_id=area_id, storage_id="")[:-1]
        try:
            config = file_study.tree.get(path.split("/"), depth=3)
            storages = {}
            for sts in config.values():
                storage = parse_st_storage(file_study.config.version, sts)
                storages[storage.id] = storage
            return storages
        except ChildNotFoundError:
            raise AreaNotFound(area_id) from None
        except KeyError:
            raise STStorageConfigNotFound(path, area_id) from None

    def _update_st_storage_config(self, area_id: str, storage: STStorage) -> None:
        study_data = self.get_file_study().config
        if area_id not in study_data.areas:
            raise ValueError(f"The area '{area_id}' does not exist")

        for k, existing_storage in enumerate(study_data.areas[area_id].st_storages):
            if existing_storage.id == storage.id:
                study_data.areas[area_id].st_storages[k] = storage
                return
        study_data.areas[area_id].st_storages.append(storage)
        if study_data.version >= STUDY_VERSION_9_2:
            study_data.areas[area_id].st_storages_additional_constraints[storage.id] = []

    def _update_st_storage_additional_constraints_config(
        self, area_id: str, storage_id: str, constraints: list[STStorageAdditionalConstraint]
    ) -> None:
        area = self.get_file_study().config.areas[area_id]
        area.st_storages_additional_constraints.setdefault(storage_id, [])
        existing_constraints = area.st_storages_additional_constraints[storage_id]
        existing_ids = {c.id: c for c in existing_constraints}
        for constraint in constraints:
            if constraint.id in existing_ids:
                area.st_storages_additional_constraints[storage_id].remove(existing_ids[constraint.id])
            area.st_storages_additional_constraints[storage_id].append(constraint)

    def _remove_st_storage_from_scenario_builder(self, area_id: str, storage_id: str) -> None:
        study_data = self.get_file_study()
        rulesets = study_data.tree.get(["settings", "scenariobuilder"])

        for ruleset in rulesets.values():
            for key in list(ruleset):
                symbol, *parts = key.split(",")
                if symbol in {"sts", "sta"} and parts[0] == area_id and parts[2] == storage_id:
                    del ruleset[key]

        study_data.tree.save(rulesets, ["settings", "scenariobuilder"])

    def _remove_st_storage_constraints_from_scenario_builder(
        self, area_id: str, storage_id: str, constraint_ids: set[str]
    ) -> None:
        study_data = self.get_file_study()
        rulesets = study_data.tree.get(["settings", "scenariobuilder"])

        for ruleset in rulesets.values():
            for key in list(ruleset):
                symbol, *parts = key.split(",")
                if symbol == "sta" and parts[0] == area_id and parts[2] == storage_id and parts[3] in constraint_ids:
                    del ruleset[key]

        study_data.tree.save(rulesets, ["settings", "scenariobuilder"])
