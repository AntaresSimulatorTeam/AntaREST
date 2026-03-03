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


from typing_extensions import override

from antarest.blobstore.blob_usage_provider import IBlobUsageProvider
from antarest.blobstore.repository import compute_blob_hash
from antarest.blobstore.service import IBlobService


class InMemoryBlobService(IBlobService):
    """
    In memory implementation of blob service, for unit testing purposes.
    """

    def __init__(self) -> None:
        self._content: dict[str, bytes] = {}
        self.usage_providers: list[IBlobUsageProvider] = []

    @override
    def save(self, data: bytes) -> str:
        blob_hash = compute_blob_hash(data)
        self._content[blob_hash] = data
        return blob_hash

    @override
    def get(self, blob_id: str) -> bytes:
        return self._content[blob_id]

    @override
    def delete(self, blob_id: str) -> None:
        del self._content[blob_id]

    @override
    def register_usage_provider(self, usage_provider: IBlobUsageProvider) -> None:
        self.usage_providers.append(usage_provider)
