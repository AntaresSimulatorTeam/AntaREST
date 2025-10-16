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


import pytest

from antarest.blobstore.exceptions import BlobNotFound
from antarest.blobstore.repository import compute_blob_hash
from antarest.blobstore.service import BlobService


def test_hashing_method():
    """
    Non-Regression Test for the hashing method
    """
    assert compute_blob_hash(b"Hello World!") == "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"

    assert (
        compute_blob_hash(b"1.0,2.3\t4.5,6.7\t") == "be8bf88e49cea435fcb733fc623836d7e0a22d3b8b579688627565a383991052"
    )


def test_lifecycle(simple_blob_service: BlobService):
    bucket_dir = simple_blob_service.blob_content_repository.bucket_dir

    # Create 2 blobs
    content_1 = b"Hello World !"
    content_2 = b"1.0,2.3\t4.5,6.7\t"
    blob_1 = simple_blob_service.create(content_1)
    blob_2 = simple_blob_service.create(content_2)

    # Ensures 2 files were created
    assert len(list(bucket_dir.iterdir())) == 2

    # Fetches data for the 2 blobs
    assert simple_blob_service.get(blob_1) == content_1
    assert simple_blob_service.get(blob_2) == content_2

    # Try to fetch a fake file
    with pytest.raises(BlobNotFound, match="Blob fake_id doesn't exist"):
        simple_blob_service.get("fake_id")

    # Deletes one blob
    simple_blob_service.delete(blob_1)

    # Ensures there's only 1 file left
    assert len(list(bucket_dir.iterdir())) == 1

    # Delete a fake blob doesn't raise
    simple_blob_service.delete("fake_id")

    # Save 2 other blobs to test `get_saved_blobs` method
    blob_3 = simple_blob_service.create(b"Content 3")
    blob_4 = simple_blob_service.create(b"Content 4")

    assert sorted(simple_blob_service.get_saved_blobs()) == sorted([blob_2, blob_3, blob_4])


# todo:
"""
test get_used
"""
