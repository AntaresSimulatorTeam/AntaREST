from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.study_upgrader import upgrade_820
from tests.storage.business.test_study_version_upgrader import are_same_dir
from tests.storage.study_upgrader.conftest import StudyAssets


def test_nominal_case(study_assets: StudyAssets):
    """
    Check that `settings/generaldata.ini` is upgraded to version 820.
    """

    # upgrade the study
    upgrade_820(study_assets.study_dir)

    # compare generaldata.ini
    actual_path = study_assets.study_dir.joinpath("settings/generaldata.ini")
    actual = IniReader().read(actual_path)
    expected_path = study_assets.expected_dir.joinpath(
        "settings/generaldata.ini"
    )
    expected = IniReader().read(expected_path)
    assert actual == expected

    # compare links
    actual_link_path = study_assets.study_dir.joinpath("input/links")
    expected_link_path = study_assets.expected_dir.joinpath("input/links")
    assert are_same_dir(actual_link_path, expected_link_path)
