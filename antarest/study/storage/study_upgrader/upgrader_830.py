import glob
from pathlib import Path
from typing import cast

from antarest.study.storage.antares_configparser import (
    AntaresConfigParser,
    AntaresSectionProxy,
)

GENERAL_DATA_PATH = Path("settings") / "generaldata.ini"
ADEQUACY_PATCH = "adequacy patch"


def upgrade_830(study_path: Path) -> None:
    config = AntaresConfigParser()
    config.read(study_path / GENERAL_DATA_PATH)
    config.add_section(ADEQUACY_PATCH)
    adequacy_patch = cast(AntaresSectionProxy, config[ADEQUACY_PATCH])
    adequacy_patch["include-adq-patch"] = False
    adequacy_patch[
        "set-to-null-ntc-between-physical-out-for-first-step"
    ] = True
    adequacy_patch[
        "set-to-null-ntc-from-physical-out-to-physical-in-for-first-step"
    ] = True
    optimization = cast(AntaresSectionProxy, config["optimization"])
    optimization["include-split-exported-mps"] = False
    with open(study_path / GENERAL_DATA_PATH, "w") as configfile:
        config.write(configfile)
    areas = glob.glob(str(study_path / "input" / "areas" / "*"))
    if len(areas) > 0:
        for folder in areas:
            folder_path = Path(folder)
            if folder_path.is_dir():
                config = AntaresConfigParser()
                config.read(
                    {"adequacy-patch": {"adequacy-patch-mode": "outside"}}
                )
                with open(folder_path / "adequacy_patch.ini", "w") as f:
                    config.write(f)
