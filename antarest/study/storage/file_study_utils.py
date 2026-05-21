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
import logging
import shutil
import time
from pathlib import Path
from typing import Sequence

from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.utils import StudyMetadataCreation, format_timestamp
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy

logger = logging.getLogger(__name__)


def get_study_path(study: Study) -> Path:
    if isinstance(study, VariantStudy):
        return get_snapshot_dir(study)
    return Path(study.path)


def get_snapshot_dir(study: VariantStudy) -> Path:
    return Path(study.path) / "snapshot"


def export_study_to_flat_directory(study_dir: Path, dest: Path) -> None:
    start_time = time.time()

    def ignore_outputs(directory: str, _: Sequence[str]) -> Sequence[str]:
        return ["output"] if str(directory) == str(study_dir) else []

    shutil.copytree(src=study_dir, dst=dest, ignore=ignore_outputs)

    stop_time = time.time()
    duration = f"{stop_time - start_time:.3f}"
    logger.info(f"Study '{study_dir}' exported (flat mode) in {duration}s")


def update_antares_info(
    metadata: Study | StudyMetadataCreation, study_tree: FileStudyTree, update_author: bool
) -> None:
    """
    Update antares study information in the study.antares file.

    Args:
        metadata: Study metadata containing name, dates, etc.
        study_tree: File study tree to update
        update_author: Whether to update the author field
    """
    study_data_info = study_tree.get(["study"])
    antares_info = study_data_info["antares"]

    author = metadata.author
    editor = metadata.editor

    # Update basic fields
    antares_info["caption"] = metadata.name
    antares_info["created"] = format_timestamp(metadata.created_at)
    antares_info["lastsave"] = format_timestamp(metadata.updated_at)
    antares_info["editor"] = editor

    # Update author-related fields if additional_data exists
    if update_author:
        antares_info["author"] = author

    study_tree.save(study_data_info, ["study"])
