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
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import Study
from antarest.study.storage.database_storage import DatabaseStudyStorage
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.snapshot.snapshot_manager_interface import ISnapshotManager


class DatabaseSnapshotManager(ISnapshotManager):
    def __init__(self, database_study_storage: DatabaseStudyStorage) -> None:
        self._database_study_storage = database_study_storage

    @override
    def is_snapshot_up_to_date(self, study: VariantStudy) -> bool:
        return self.has_snapshot(study) and (study.snapshot.created_at >= study.updated_at)

    @override
    def has_snapshot(self, study: VariantStudy) -> bool:
        return study.snapshot is not None

    @override
    def create_snapshot(self, ref_study: Study, variant_study: VariantStudy) -> None:
        # TODO: Uncomment the first line
        # self.clear_snapshot(variant_study)
        self._database_study_storage.copy_study(ref_study, variant_study)

    @override
    def clear_snapshot(self, variant_study: VariantStudy) -> None:
        session: Session = db.session
        # First, remove the VariantStudy from the DB to remove all associated data via cascade deletion.
        session.delete(variant_study)
        session.commit()
        # Then, re-insert the VariantStudy. This time, it will be empty.
        session.add(variant_study)
        session.commit()
