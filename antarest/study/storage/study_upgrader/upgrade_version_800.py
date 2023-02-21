from pathlib import Path
from typing import cast

from antarest.study.storage.antares_configparser import (
    AntaresConfigParser,
    AntaresSectionProxy,
)

OTHER_PREFERENCES = "other preferences"
GENERAL_DATA_PATH = Path("settings") / "generaldata.ini"


def _upgrade_800(study_path: Path) -> None:
    config = AntaresConfigParser()
    config.read(study_path / GENERAL_DATA_PATH)
    config[OTHER_PREFERENCES][
        "hydro-heuristic-policy"
    ] = "accommodate rule curves"
    optimization = cast(AntaresSectionProxy, config["optimization"])
    optimization["include-exportstructure"] = False
    optimization["include-unfeasible-problem-behavior"] = "error-verbose"
    config["general"]["custom-scenario"] = config["general"][
        "custom-ts-numbers"
    ]
    config.remove_option("general", "custom-ts-numbers")
    with open(study_path / GENERAL_DATA_PATH, "w") as configfile:
        config.write(configfile)
