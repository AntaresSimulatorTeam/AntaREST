from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.study_upgrader import upgrade_850
from tests.storage.study_upgrader.conftest import StudyAssets


# noinspection SpellCheckingInspection
def test_nominal_case(study_assets: StudyAssets):
    """
    Check that `settings/generaldata.ini` is upgraded to version 850.
    """

    # upgrade the study
    upgrade_850(study_assets.study_dir)

    # compare generaldata.ini
    actual_path = study_assets.study_dir.joinpath("settings/generaldata.ini")
    actual = IniReader().read(actual_path)
    expected_path = study_assets.expected_dir.joinpath("settings/generaldata.ini")
    expected = IniReader().read(expected_path)
    assert actual == expected
