from antarest.study.storage.study_upgrader import upgrade_860
from tests.storage.business.test_study_version_upgrader import are_same_dir
from tests.storage.study_upgrader.conftest import StudyAssets


def test_upgrade_860(study_assets: StudyAssets):
    """
    Check that 'st-storage' folder is created and filled.
    """

    # upgrade the study
    upgrade_860(study_assets.study_dir)

    # compare input folder
    actual_input_path = study_assets.study_dir.joinpath("input")
    expected_input_path = study_assets.expected_dir.joinpath("input")
    assert are_same_dir(actual_input_path, expected_input_path)
