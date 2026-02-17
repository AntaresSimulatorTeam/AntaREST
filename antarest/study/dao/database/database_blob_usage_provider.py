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
from typing import Iterable

from sqlalchemy import select
from typing_extensions import override

from antarest.blobstore.blob_usage_provider import IBlobUsageProvider
from antarest.blobstore.model import BlobReference
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.dao.database.models.user_resources import USER_RESOURCES_TABLE


class DatabaseBlobUsageProvider(IBlobUsageProvider):
    @override
    def get_blob_usage(self) -> Iterable[BlobReference]:
        with db():
            stmt = select(USER_RESOURCES_TABLE).where(USER_RESOURCES_TABLE.c.blob_id.isnot(None))
            rows = db.session.execute(stmt).fetchall()
            for row in rows:
                yield BlobReference(blob_id=row.blob_id, use_description=f"Used by study {row.study_id}")
