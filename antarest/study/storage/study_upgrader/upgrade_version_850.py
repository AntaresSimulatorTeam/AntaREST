from pathlib import Path
from typing import cast

from antarest.study.storage.antares_configparser import (
    AntaresConfigParser,
    AntaresSectionProxy,
)

GENERAL_DATA_PATH = Path("settings") / "generaldata.ini"
ADEQUACY_PATCH = "adequacy patch"


def _upgrade_850(study_path: Path) -> None:
    config = AntaresConfigParser()
    config.read(study_path / GENERAL_DATA_PATH)
    adequacy_patch = cast(AntaresSectionProxy, config[ADEQUACY_PATCH])
    adequacy_patch["price-taking-order"] = "DENS"
    adequacy_patch["include-hurdle-cost-csr"] = False
    adequacy_patch["check-csr-cost-function"] = False
    adequacy_patch["threshold-initiate-curtailment-sharing-rule"] = 0.0
    adequacy_patch["threshold-display-local-matching-rule-violations"] = 0.0
    adequacy_patch["threshold-csr-variable-bounds-relaxation"] = 3
    with open(study_path / GENERAL_DATA_PATH, "w") as configfile:
        config.write(configfile)
