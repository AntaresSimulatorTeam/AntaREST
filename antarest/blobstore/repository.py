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

import hashlib
import logging
from pathlib import Path

from antarest.blobstore.exceptions import BlobNotFound

logger = logging.getLogger(__name__)


def compute_blob_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class BlobContentRepository:
    def __init__(self, bucket_dir: Path) -> None:
        self.bucket_dir = bucket_dir
        self.bucket_dir.mkdir(parents=True, exist_ok=True)

    def get(self, blob_hash: str) -> bytes:
        file_path = self.bucket_dir / blob_hash
        if not file_path.exists():
            raise BlobNotFound(blob_hash)
        return file_path.read_bytes()

    def save(self, content: bytes) -> str:
        blob_hash = compute_blob_hash(content)
        file_path = self.bucket_dir / blob_hash
        if not file_path.exists():
            file_path.write_bytes(content)
        return blob_hash

    def delete(self, blob_hash: str) -> None:
        (self.bucket_dir / blob_hash).unlink(missing_ok=True)

    def get_all(self) -> list[str]:
        return [file.name for file in self.bucket_dir.iterdir()]
