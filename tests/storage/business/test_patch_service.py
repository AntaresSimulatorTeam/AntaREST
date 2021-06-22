from unittest.mock import Mock, ANY, patch

import pytest

from antarest.storage.business.patch_service import PatchService
from antarest.storage.model import RawStudy, Patch
from antarest.storage.repository.patch_repository import PatchRepository
from antarest.storage.service import StorageService


@pytest.mark.unit_test
def test_get():
    raw_study = Mock(spec=RawStudy)

    expected_patch = Mock(spec=Patch)
    patch_repository = Mock(spec=PatchRepository)
    patch_repository.get.return_value = expected_patch

    patch_service = PatchService(repository=patch_repository)

    output = patch_service.get(study=raw_study)

    patch_repository.get.assert_called_once_with(raw_study)
    assert output == expected_patch


@pytest.mark.unit_test
def test_set_reference_output():
    raw_study = Mock(spec=RawStudy)

    patch = Mock()
    patch_repository = Mock(spec=PatchRepository)
    patch_repository.get.return_value = patch

    patch_service = PatchService(repository=patch_repository)

    output_id = "output_id"

    patch_service.set_reference_output(study=raw_study, output_id=output_id)

    patch_repository.get.assert_called_once_with(raw_study)
    assert patch.outputs.reference == output_id
    patch_repository.save.assert_called_once_with(raw_study, patch)


@pytest.mark.unit_test
def test_patch():
    new_patch_content = {"study": {"scenario": "BAU2025"}}
    new_patch = Patch.parse_obj(new_patch_content)

    raw_study = Mock(spec=RawStudy)

    patch_repository = Mock(spec=PatchRepository)

    patch_service = PatchService(repository=patch_repository)

    patch_service.patch(study=raw_study, new_patch_content=new_patch_content)

    patch_repository.patch.assert_called_once_with(raw_study, new_patch)
