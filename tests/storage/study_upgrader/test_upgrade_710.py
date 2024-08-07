from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.study_upgrader import StudyUpgrader
from tests.storage.study_upgrader.conftest import StudyAssets


def test_nominal_case(study_assets: StudyAssets):
    """
    Check that `settings/generaldata.ini` is upgraded to version 710.
    """

    # upgrade the study
    study_upgrader = StudyUpgrader(study_assets.study_dir, "710")
    study_upgrader.upgrade()

    # compare generaldata.ini
    actual_path = study_assets.study_dir.joinpath("settings/generaldata.ini")
    actual = IniReader().read(actual_path)
    expected_path = study_assets.expected_dir.joinpath("settings/generaldata.ini")
    expected = IniReader().read(expected_path)
    assert actual == expected
