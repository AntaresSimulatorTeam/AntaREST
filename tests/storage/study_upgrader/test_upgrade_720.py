from antarest.study.storage.study_upgrader import upgrade_720
from tests.storage.business.test_study_version_upgrader import are_same_dir
from tests.storage.study_upgrader.conftest import StudyAssets


def test_nominal_case(study_assets: StudyAssets):
    """
    Check that `settings/generaldata.ini` is upgraded to version 720.
    """

    # upgrade the study
    upgrade_720(study_assets.study_dir)

    # compare folder
    assert are_same_dir(study_assets.study_dir, study_assets.expected_dir)
