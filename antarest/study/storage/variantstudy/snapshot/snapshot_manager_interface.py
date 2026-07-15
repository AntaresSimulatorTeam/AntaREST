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

from sqlalchemy import select

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import Study
from antarest.study.storage.variantstudy.model.dbmodel import COMMANDS_LIST_VERSION_TABLE, VariantStudy


class ISnapshotManager(ABC):
    @staticmethod
    def is_snapshot_up_to_date(study: VariantStudy) -> bool:
        # Snapshot version
        if not study.snapshot:
            return False
        snapshot_version: int = study.snapshot.version

        # Commands list version
        query = select(COMMANDS_LIST_VERSION_TABLE).where(COMMANDS_LIST_VERSION_TABLE.c.variant_id == study.id)
        commands_list_version: int = db.session.execute(query).one()._asdict()["version"]

        return commands_list_version == snapshot_version

    @abstractmethod
    def has_snapshot(self, study: VariantStudy) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def create_snapshot(self, ref_study: Study, variant_study: VariantStudy) -> None:
        raise NotImplementedError()

    @abstractmethod
    def clear_snapshot(self, variant_study: VariantStudy) -> None:
        raise NotImplementedError()
