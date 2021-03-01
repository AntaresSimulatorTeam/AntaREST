from pathlib import Path

import pytest

from antarest.storage.business.storage_service_utils import StorageServiceUtils
from antarest.storage.web.exceptions import StudyValidationError


@pytest.mark.unit_test
def test_check_antares_version(
    tmp_path: Path, storage_service_builder
) -> None:

    right_study = {"study": {"antares": {"version": 700}}}
    StorageServiceUtils.check_antares_version(right_study)

    wrong_study = {"study": {"antares": {"version": 600}}}
    with pytest.raises(StudyValidationError):
        StorageServiceUtils.check_antares_version(wrong_study)
