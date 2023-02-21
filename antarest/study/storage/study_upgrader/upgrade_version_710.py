from pathlib import Path
from typing import cast

from antarest.study.storage.antares_configparser import (
    AntaresConfigParser,
    AntaresSectionProxy,
)

OTHER_PREFERENCES = "other preferences"
GENERAL_DATA_PATH = Path("settings") / "generaldata.ini"


def _upgrade_710(study_path: Path) -> None:
    config = AntaresConfigParser()
    config.read(study_path / GENERAL_DATA_PATH)
    general = cast(AntaresSectionProxy, config["general"])
    general["geographic-trimming"] = config["general"]["filtering"]
    general["thematic-trimming"] = False
    config["optimization"]["link-type"] = "local"
    config[OTHER_PREFERENCES]["hydro-pricing-mode"] = "fast"
    config.remove_option("general", "filtering")
    with open(study_path / GENERAL_DATA_PATH, "w") as configfile:
        config.write(configfile)
