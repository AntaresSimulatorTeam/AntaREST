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
import uuid
from unittest.mock import Mock

import pytest

from antarest.blobstore.exceptions import BlobNotFound
from antarest.blobstore.model import BlobReference
from antarest.blobstore.repository import compute_blob_hash
from antarest.blobstore.service import BlobService
from antarest.study.storage.variantstudy.command_blob_usage_provider import CommandBlobUsageProvider
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock
from antarest.study.storage.variantstudy.repository import VariantStudyRepository


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
    blob_1 = simple_blob_service.save(content_1)
    blob_2 = simple_blob_service.save(content_2)

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
    blob_3 = simple_blob_service.save(b"Content 3")
    blob_4 = simple_blob_service.save(b"Content 4")

    assert sorted(simple_blob_service.get_saved_blobs()) == sorted([blob_2, blob_3, blob_4])


def test_get_used_blobs(command_factory: CommandFactory) -> None:
    # Create a Mock with 4 commands.
    # Only 2 blobs should be returned as the other commands didn't create any blob inside the blob store.
    mock_repo = Mock(spec=VariantStudyRepository)
    study_id = str(uuid.uuid4())
    cmd_id_1 = str(uuid.uuid4())
    cmd_id_2 = str(uuid.uuid4())
    mock_repo.get_all_command_blocks.return_value = [
        CommandBlock(
            id=cmd_id_1,
            study_id=study_id,
            index=0,
            version=2,
            study_version="9.3",
            command="replace_user_resource",
            args='{"data": {"resource_type": "file", "path": "file.txt", "blob_id": "blob_1"}}',
        ),
        CommandBlock(
            id=cmd_id_2,
            study_id=study_id,
            index=1,
            version=1,
            study_version="9.3",
            command="replace_user_resource",
            args='{"data": {"resource_type": "file", "path": "file2.txt", "content": "Hello World !"}}',
        ),
        CommandBlock(
            id=str(uuid.uuid4()),
            study_id=study_id,
            index=2,
            version=2,
            study_version="9.3",
            command="replace_user_resource",
            args='{"data": {"resource_type": "folder", "path": "new_folder"}}',
        ),
        CommandBlock(
            id=str(uuid.uuid4()),
            study_id=study_id,
            index=3,
            version=1,
            study_version="9.3",
            command="remove_area",
            args='{"id": "fr"}',
        ),
    ]

    blob_service: BlobService = command_factory.command_context.blob_service
    # Ensures without a provider, there are no used blobs
    assert len(list(blob_service.get_used_blobs())) == 0

    # Adds the provider. Instantiating it adds it to the service
    CommandBlobUsageProvider(variant_study_repo=mock_repo, command_factory=command_factory)

    # Ensures 2 blobs are returned
    used_blobs = list(blob_service.get_used_blobs())
    assert len(used_blobs) == 2
    expected_generated_blob_id = "07f2bdef34ed16e3a1ba0dbb7e47b8fd981ce0ccb3e1bfe564d82c423cba7e47"
    assert used_blobs[0] == BlobReference(
        blob_id="blob_1", use_description=f"Used by command {cmd_id_1} from variant study {study_id}"
    )
    assert used_blobs[1] == BlobReference(
        blob_id=expected_generated_blob_id, use_description=f"Used by command {cmd_id_2} from variant study {study_id}"
    )
