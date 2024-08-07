from antarest.study.storage.study_upgrader import StudyUpgrader
from tests.storage.business.test_study_version_upgrader import are_same_dir
from tests.storage.study_upgrader.conftest import StudyAssets


def test_nominal_case(study_assets: StudyAssets):
    """
    Check that binding constraints and thermal folders are correctly modified
    """

    # upgrade the study
    study_upgrader = StudyUpgrader(study_assets.study_dir, "870")
    study_upgrader.upgrade()

    # compare input folders (bindings + thermals)
    actual_input_path = study_assets.study_dir.joinpath("input")
    expected_input_path = study_assets.expected_dir.joinpath("input")
    assert are_same_dir(actual_input_path, expected_input_path)


def test_empty_binding_constraints(study_assets: StudyAssets):
    """
    Check that binding constraints and thermal folders are correctly modified
    """

    # upgrade the study
    study_upgrader = StudyUpgrader(study_assets.study_dir, "870")
    study_upgrader.upgrade()

    # compare input folders (bindings + thermals)
    actual_input_path = study_assets.study_dir.joinpath("input")
    expected_input_path = study_assets.expected_dir.joinpath("input")
    assert are_same_dir(actual_input_path, expected_input_path)
