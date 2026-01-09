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
from typing import Iterable, List

from typing_extensions import override

from antarest.blobstore.blob_usage_provider import IBlobUsageProvider
from antarest.blobstore.model import BlobReference
from antarest.blobstore.repository import BlobContentRepository


class IBlobService(ABC):
    @abstractmethod
    def save(self, data: bytes) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get(self, blob_id: str) -> bytes:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, blob_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def register_usage_provider(self, usage_provider: IBlobUsageProvider) -> None:
        raise NotImplementedError()


class BlobService(IBlobService):
    def __init__(
        self,
        blob_content_repository: BlobContentRepository,
    ):
        self.blob_content_repository = blob_content_repository
        self.usage_providers: List[IBlobUsageProvider] = []

    @override
    def save(self, data: bytes) -> str:
        return self.blob_content_repository.save(data)

    @override
    def get(self, blob_id: str) -> bytes:
        return self.blob_content_repository.get(blob_id)

    @override
    def delete(self, blob_id: str) -> None:
        self.blob_content_repository.delete(blob_id)

    @override
    def register_usage_provider(self, usage_provider: IBlobUsageProvider) -> None:
        self.usage_providers.append(usage_provider)

    def get_used_blobs(self) -> Iterable[BlobReference]:
        """Return all blobs used in variant studies"""
        for provider in self.usage_providers:
            yield from provider.get_blob_usage()

    def get_saved_blobs(self) -> list[str]:
        """Return all saved blobs in the content repository"""
        return self.blob_content_repository.get_all()
