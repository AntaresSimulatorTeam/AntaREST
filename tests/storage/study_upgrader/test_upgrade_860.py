from pathlib import Path

from antarest.study.storage.study_upgrader import upgrade_860


def test_upgrade_860():
    cur_dir: Path = Path(__file__).parent.parent
    path_study = cur_dir / "business" / "assets" / "little_study_720"

    upgrade_860(path_study)