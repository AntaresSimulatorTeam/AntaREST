from http import HTTPStatus
from http.client import HTTPException
from pathlib import Path
from typing import NamedTuple, Callable
import logging
import re
import shutil
import tempfile
import time

from antarest.core.exceptions import StudyValidationError

from .upgrader_710 import upgrade_710
from .upgrader_720 import upgrade_720
from .upgrader_800 import upgrade_800
from .upgrader_810 import upgrade_810
from .upgrader_820 import upgrade_820
from .upgrader_830 import upgrade_830
from .upgrader_840 import upgrade_840
from .upgrader_850 import upgrade_850


logger = logging.getLogger(__name__)


class UpgradeMethod(NamedTuple):
    """Raw study upgrade method (old version, new version, upgrade function)."""

    old: str
    new: str
    method: Callable[[Path], None]


UPGRADE_METHODS = [
    UpgradeMethod("700", "710", upgrade_710),
    UpgradeMethod("710", "720", upgrade_720),
    UpgradeMethod("720", "800", upgrade_800),
    UpgradeMethod("800", "810", upgrade_810),
    UpgradeMethod("810", "820", upgrade_820),
    UpgradeMethod("820", "830", upgrade_830),
    UpgradeMethod("830", "840", upgrade_840),
    UpgradeMethod("840", "850", upgrade_850),
]


class InvalidUpgrade(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


def find_next_version(from_version: str) -> str:
    """
    Find the next study version from the given version.

    Args:
        from_version: The current version as a string.

    Returns:
        The next version as a string.
        If no next version was found, returns an empty string.
    """
    return next(
        (meth.new for meth in UPGRADE_METHODS if from_version == meth.old),
        "",
    )


def upgrade_study(study_path: Path, target_version: str) -> None:
    tmp_dir = Path(
        tempfile.mkdtemp(
            suffix=".upgrade.tmp", prefix="~", dir=study_path.parent
        )
    )
    shutil.copytree(study_path, tmp_dir, dirs_exist_ok=True)
    try:
        src_version = get_current_version(tmp_dir)
        can_upgrade_version(src_version, target_version)
        _do_upgrade(tmp_dir, src_version, target_version)
    except (StudyValidationError, InvalidUpgrade) as e:
        shutil.rmtree(tmp_dir)
        logger.warning(str(e))
        raise
    except Exception as e:
        shutil.rmtree(tmp_dir)
        logger.error(f"Unhandled exception : {e}", exc_info=True)
        raise
    else:
        backup_dir = Path(
            tempfile.mkdtemp(
                suffix=".backup.tmp", prefix="~", dir=study_path.parent
            )
        )
        backup_dir.rmdir()
        study_path.rename(backup_dir)
        tmp_dir.rename(study_path)
        shutil.rmtree(backup_dir, ignore_errors=True)


def get_current_version(study_path: Path) -> str:
    """
    Get the current version of a study.

    Args:
        study_path: Path to the study.

    Returns:
        The current version of the study.

    Raises:
        StudyValidationError: If the version number is not found in the
        `study.antares` file or does not match the expected format.
    """

    antares_path = study_path / "study.antares"
    pattern = r"version\s*=\s*([\w.-]+)\s*"
    with antares_path.open(encoding="utf-8") as lines:
        for line in lines:
            if match := re.fullmatch(pattern, line):
                return match[1].rstrip()
    raise StudyValidationError(
        f"File parsing error: the version number is not found in '{antares_path}'"
        f" or does not match the expected '{pattern}' format."
    )


def can_upgrade_version(from_version: str, to_version: str) -> None:
    """
    Checks if upgrading from one version to another is possible.

    Args:
        from_version: The current version of the study.
        to_version: The target version of the study.

    Raises:
        InvalidUpgrade: If the upgrade is not possible.
    """
    if from_version == to_version:
        raise InvalidUpgrade(
            f"Your study is already in version '{to_version}'"
        )

    sources = [u.old for u in UPGRADE_METHODS]
    if from_version not in sources:
        raise InvalidUpgrade(
            f"Version '{from_version}' unknown: possible versions are {', '.join(sources)}"
        )

    targets = [u.new for u in UPGRADE_METHODS]
    if to_version not in targets:
        raise InvalidUpgrade(
            f"Version '{to_version}' unknown: possible versions are {', '.join(targets)}"
        )

    curr_version = from_version
    for src, dst in zip(sources, targets):
        if curr_version == src:
            curr_version = dst
        if curr_version == to_version:
            return

    # This code must be unreachable!
    raise InvalidUpgrade(
        f"Impossible to upgrade from version '{from_version}'"
        f" to version '{to_version}':"
        f" missing value in `UPGRADE_METHODS`."
    )


def _update_study_antares_file(target_version: str, study_path: Path) -> None:
    file = study_path / "study.antares"
    content = file.read_text(encoding="utf-8")
    content = re.sub(
        r"^version\s*=.*$",
        f"version = {target_version}",
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r"^lastsave\s*=.*$",
        f"lastsave = {int(time.time())}",
        content,
        flags=re.MULTILINE,
    )
    file.write_text(content, encoding="utf-8")


def _do_upgrade(
    study_path: Path, src_version: str, target_version: str
) -> None:
    _update_study_antares_file(target_version, study_path)
    curr_version = src_version
    for old, new, method in UPGRADE_METHODS:
        if curr_version == old and curr_version != target_version:
            method(study_path)
            curr_version = new
