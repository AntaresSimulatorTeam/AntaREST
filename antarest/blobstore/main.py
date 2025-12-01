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

from typing import Optional

from antarest.blobstore.repository import BlobContentRepository
from antarest.blobstore.service import BlobService
from antarest.core.config import Config


def build_blob_service(config: Config, service: Optional[BlobService] = None) -> BlobService:
    if service is None:
        content = BlobContentRepository(config.storage.blobstore)
        service = BlobService(blob_content_repository=content)

    return service
