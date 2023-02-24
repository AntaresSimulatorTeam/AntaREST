from antarest.study.storage.study_upgrader import _upgrade_850 as upgrade_850
from tests.storage.study_upgrader.conftest import StudyAssets


def test_nominal_case(study_assets: StudyAssets):
    # upgrade the study
    upgrade_850(study_assets.study_dir)

    # compare with expected
    # todo: compare with `study_assets.expected_dir`
