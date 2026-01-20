# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.blobstore.blob_garbage_collector import BlobGarbageCollector
from antarest.blobstore.model import BlobReference
from antarest.blobstore.service import BlobService


@pytest.fixture
def blob_garbage_collector(tmp_path: Path) -> BlobGarbageCollector:
    """
    Fixture for creating a BlobGarbageCollector object.
    """
    return BlobGarbageCollector(blob_service=Mock(), dry_run=False, sleeping_time=3600)


def test_delete_unused_saved_blobs(
    blob_garbage_collector: BlobGarbageCollector,
) -> None:
    unused_blobs = {"blob1", "blob2"}
    blob_garbage_collector.blob_service.delete = Mock()
    blob_garbage_collector._delete_unused_saved_blobs(unused_blobs)

    blob_garbage_collector.blob_service.delete.assert_any_call("blob1")
    blob_garbage_collector.blob_service.delete.assert_any_call("blob2")

    blob_garbage_collector.dry_run = True
    blob_garbage_collector.blob_service.delete.reset_mock()
    blob_garbage_collector._delete_unused_saved_blobs(unused_blobs)
    blob_garbage_collector.blob_service.delete.assert_not_called()


def test_clean_blobs(blob_garbage_collector: BlobGarbageCollector) -> None:
    blob_garbage_collector.blob_service.get_saved_blobs.return_value = ["blob_saved", "blob_used"]
    blob_garbage_collector.blob_service.get_used_blobs.return_value = [
        BlobReference(blob_id="blob_used", use_description="Used in variant 1")
    ]
    blob_garbage_collector._delete_unused_saved_blobs = Mock()

    blob_garbage_collector.clean_blobs()

    blob_garbage_collector._delete_unused_saved_blobs.assert_called_once_with(unused_blobs={"blob_saved"})


def test_clean_matrices_with_actual_service(simple_blob_service: BlobService) -> None:
    gc = BlobGarbageCollector(blob_service=simple_blob_service, sleeping_time=3600, dry_run=False)

    blob_id = simple_blob_service.save(b"Hello World !")
    assert simple_blob_service.get_saved_blobs() == [blob_id]

    gc.clean_blobs()
    assert list(simple_blob_service.get_used_blobs()) == []
