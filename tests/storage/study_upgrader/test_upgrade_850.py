from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.study_upgrader import upgrade_850 as upgrade_850
from tests.storage.study_upgrader.conftest import StudyAssets


# noinspection SpellCheckingInspection
def test_nominal_case(study_assets: StudyAssets):
    """
    Check that `settings/generaldata.ini` is upgraded to version 850.
    """
    # study_antares_path = study_assets.study_dir.joinpath("study.antares")
    # old_lastsave = float(IniReader().read(study_antares_path)["antares"]["lastsave"])

    # upgrade the study
    upgrade_850(study_assets.study_dir)

    # # compare study.antares
    # actual_path = study_assets.study_dir.joinpath("study.antares")
    # actual = IniReader().read(actual_path)
    # expected_path = study_assets.expected_dir.joinpath("study.antares")
    # expected = IniReader().read(expected_path)
    # assert expected["antares"]["version"] == 850
    # assert actual["antares"]["caption"] == expected["antares"]["caption"]
    # assert actual["antares"]["created"] == expected["antares"]["created"]
    # assert float(actual["antares"]["lastsave"]) > old_lastsave
    # assert actual["antares"]["author"] == expected["antares"]["author"]

    # compare generaldata.ini
    # fmt: off
    actual_path = study_assets.study_dir.joinpath("settings/generaldata.ini")
    actual = IniReader().read(actual_path)
    expected_path = study_assets.expected_dir.joinpath("settings/generaldata.ini")
    expected = IniReader().read(expected_path)
    assert actual == expected
    # fmt: on
