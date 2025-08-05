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

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, cast

import yaml
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.model import JSON
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import assert_this
from antarest.launcher.extensions.interface import ILauncherExtension
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.utils import is_managed

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from antarest.study.service import StudyService


def _prepare_study_for_adq_patch(study: FileStudy, adq_patch_config: JSON) -> Dict[str, bool]:
    area_to_turn_on: List[str] = [transform_name_to_id(area_id) for area_id in adq_patch_config.get("areas", [])]
    original_area_enabled: Dict[str, bool] = {}
    original_link_enabled: Dict[str, bool] = {}
    year_by_year_active = study.tree.get(["settings", "generaldata", "general", "year-by-year"])
    study.tree.save(True, ["settings", "generaldata", "general", "year-by-year"])
    for area_id, area in study.config.areas.items():
        # areas
        original_area_enabled[area_id] = "hourly" in area.filters_year
        if not original_area_enabled[area_id] and area_id in area_to_turn_on:
            study.tree.save(
                ", ".join([*area.filters_year, "hourly"]),
                [
                    "input",
                    "areas",
                    area_id,
                    "optimization",
                    "filtering",
                    "filter-year-by-year",
                ],
            )

        # links
        for area_2, link in area.links.items():
            link_id = f"{area_id} - {area_2}"
            original_link_enabled[link_id] = "hourly" in link.filters_year
            if not original_link_enabled[link_id] and (area_id in area_to_turn_on or area_2 in area_to_turn_on):
                study.tree.save(
                    ", ".join([*link.filters_year, "hourly"]),
                    [
                        "input",
                        "links",
                        area_id,
                        "properties",
                        area_2,
                        "filter-year-by-year",
                    ],
                )

    with db():
        with open(
            study.config.study_path / "user" / "adequacypatch" / "hourly-areas.yml",
            "w",
        ) as fh:
            yaml.dump(original_area_enabled, fh)
        with open(
            study.config.study_path / "user" / "adequacypatch" / "hourly-links.yml",
            "w",
        ) as fh:
            yaml.dump(original_link_enabled, fh)
        if year_by_year_active:
            with open(
                study.config.study_path / "user" / "adequacypatch" / "year-by-year-active",
                "w",
            ) as fh:
                fh.write("True")

    return original_area_enabled


class AdequacyPatchExtension(ILauncherExtension):
    EXTENSION_NAME = "adequacy_patch"

    def __init__(self, study_service: StudyService, config: Config):
        self.study_service = study_service

    @override
    def get_name(self) -> str:
        return AdequacyPatchExtension.EXTENSION_NAME

    @override
    def after_export_flat_hook(
        self,
        job_id: str,
        study_id: str,
        study_export_path: Path,
        launcher_opts: Any,
    ) -> None:
        logger.info("Applying adequacy patch postprocessing script")
        study = self.study_service.storage_service.raw_study_service.study_factory.create_from_fs(
            study_export_path, is_managed(self.study_service.get_study(study_id)), study_id, use_cache=False
        )
        user_config = study.tree.get(
            ["user"],
        )
        assert_this("flowbased" in user_config)
        adequacy_patch_config = yaml.safe_load(cast(bytes, study.tree.get(["user", "adequacypatch", "config.yml"])))
        assert_this("areas" in adequacy_patch_config)
        _prepare_study_for_adq_patch(study, adequacy_patch_config)

        full_r_version = "legacy" in launcher_opts and launcher_opts["legacy"]
        if "mode" in adequacy_patch_config and adequacy_patch_config["mode"] == "legacy":
            full_r_version = True

        if full_r_version:
            logger.info("Using legacy quadratic mode")
            post_processing_file = Path(__file__).parent / "resources" / "post-processing-legacy.R"
        else:
            logger.info("Using linearized mode")
            post_processing_file = Path(__file__).parent / "resources" / "post-processing.R"
        shutil.copy(post_processing_file, study_export_path / "post-processing.R")

    @override
    def before_import_hook(
        self,
        job_id: str,
        study_id: str,
        study_output_path: Path,
        ext_opts: Any,
    ) -> None:
        pass
