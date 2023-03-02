from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.study_upgrader import upgrade_830
from tests.storage.business.test_study_version_upgrader import are_same_dir
from tests.storage.study_upgrader.conftest import StudyAssets


def test_nominal_case(study_assets: StudyAssets):
    """
    Check that `settings/generaldata.ini` is upgraded to version 830.
    """

    # upgrade the study
    upgrade_830(study_assets.study_dir)

    # compare generaldata.ini
    actual_path = study_assets.study_dir.joinpath("settings/generaldata.ini")
    actual = IniReader().read(actual_path)
    expected_path = study_assets.expected_dir.joinpath(
        "settings/generaldata.ini"
    )
    expected = IniReader().read(expected_path)
    assert actual == expected

    # compare areas
    actual_area_path = study_assets.study_dir.joinpath("input/areas")
    expected_area_path = study_assets.expected_dir.joinpath("input/areas")
    assert are_same_dir(actual_area_path, expected_area_path)
