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
from collections.abc import Iterable

from typing_extensions import override

from antarest.blobstore.blob_usage_provider import IBlobUsageProvider
from antarest.blobstore.model import BlobReference
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.dao.database.study_data_queries import yield_used_blobs


class DatabaseBlobUsageProvider(IBlobUsageProvider):
    @override
    def get_blob_usage(self) -> Iterable[BlobReference]:
        with db():
            for blob_id, study_id in yield_used_blobs(db.session):
                yield BlobReference(blob_id=blob_id, use_description=f"Used by study {study_id}")
