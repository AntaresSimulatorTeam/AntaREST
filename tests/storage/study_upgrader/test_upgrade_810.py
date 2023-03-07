from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.study_upgrader import upgrade_810
from tests.storage.business.test_study_version_upgrader import are_same_dir
from tests.storage.study_upgrader.conftest import StudyAssets


def test_nominal_case(study_assets: StudyAssets):
    """
    Check that `settings/generaldata.ini` is upgraded to version 810.
    """

    # upgrade the study
    upgrade_810(study_assets.study_dir)

    # compare generaldata.ini
    actual_path = study_assets.study_dir.joinpath("settings/generaldata.ini")
    actual = IniReader().read(actual_path)
    expected_path = study_assets.expected_dir.joinpath(
        "settings/generaldata.ini"
    )
    expected = IniReader().read(expected_path)
    assert actual == expected

    # compare folders (because the upgrade should create empty "renewables" folder)
    assert are_same_dir(
        study_assets.study_dir.joinpath("input"),
        study_assets.expected_dir.joinpath("input"),
    )
