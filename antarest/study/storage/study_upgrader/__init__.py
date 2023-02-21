from http import HTTPStatus
from http.client import HTTPException
from pathlib import Path
from typing import NamedTuple, Callable

from antarest.study.storage.study_upgrader.upgrade_version_710 import (
    _upgrade_710,
)
from antarest.study.storage.study_upgrader.upgrade_version_720 import (
    _upgrade_720,
)
from antarest.study.storage.study_upgrader.upgrade_version_800 import (
    _upgrade_800,
)
from antarest.study.storage.study_upgrader.upgrade_version_810 import (
    _upgrade_810,
)
from antarest.study.storage.study_upgrader.upgrade_version_820 import (
    _upgrade_820,
)
from antarest.study.storage.study_upgrader.upgrade_version_830 import (
    _upgrade_830,
)
from antarest.study.storage.study_upgrader.upgrade_version_840 import (
    _upgrade_840,
)
from antarest.study.storage.study_upgrader.upgrade_version_850 import (
    _upgrade_850,
)

MAPPING_TRANSMISSION_CAPACITIES = {
    True: "local-values",
    False: "null-for-all-links",
    "infinite": "infinite-for-all-links",
}


class UpgradeMethod(NamedTuple):
    """Raw study upgrade method (old version, new version, upgrade function)."""

    old: str
    new: str
    method: Callable[[Path], None]


UPGRADE_METHODS = [
    UpgradeMethod("700", "710", _upgrade_710),
    UpgradeMethod("710", "720", _upgrade_720),
    UpgradeMethod("720", "800", _upgrade_800),
    UpgradeMethod("800", "810", _upgrade_810),
    UpgradeMethod("810", "820", _upgrade_820),
    UpgradeMethod("820", "830", _upgrade_830),
    UpgradeMethod("830", "840", _upgrade_840),
    UpgradeMethod("840", "850", _upgrade_850),
]


class InvalidUpgrade(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)
