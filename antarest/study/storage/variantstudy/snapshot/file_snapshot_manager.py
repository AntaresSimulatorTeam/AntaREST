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
from pathlib import Path

from typing_extensions import override

from antarest.core.interfaces.cache import ICache
from antarest.study.model import RawStudy, Study
from antarest.study.storage.utils import export_study_to_flat_directory, remove_from_cache
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.snapshot.snapshot_manager_interface import ISnapshotManager

logger = logging.getLogger(__name__)


class FileSnapshotManager(ISnapshotManager):
    def __init__(self, cache: ICache):
        self._cache = cache

    @override
    def is_snapshot_up_to_date(self, study: VariantStudy) -> bool:
        return study.is_snapshot_up_to_date()

    @override
    def create_snapshot(self, ref_study: Study, variant_study: VariantStudy) -> None:
        remove_from_cache(self._cache, variant_study.id)
        snapshot_dir = variant_study.snapshot_dir
        logger.info(f"Exporting the reference study '{ref_study.id}' to '{snapshot_dir.name}'...")
        shutil.rmtree(snapshot_dir, ignore_errors=True)

        if isinstance(ref_study, VariantStudy):
            snapshot_dir.parent.mkdir(parents=True, exist_ok=True)
            export_study_to_flat_directory(ref_study.snapshot_dir, snapshot_dir)
        elif isinstance(ref_study, RawStudy):
            export_study_to_flat_directory(Path(ref_study.path), snapshot_dir)

    @override
    def clear_snapshot(self, variant_study: VariantStudy) -> None:
        logger.info(f"Clearing snapshot for study {variant_study.id}")
        shutil.rmtree(variant_study.snapshot_dir, ignore_errors=True)
