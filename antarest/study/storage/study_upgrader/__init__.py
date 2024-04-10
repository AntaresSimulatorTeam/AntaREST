import logging
import re
import shutil
import tempfile
import time
import typing as t
from http import HTTPStatus
from http.client import HTTPException
from pathlib import Path

from antarest.core.exceptions import StudyValidationError

from .upgrader_710 import upgrade_710
from .upgrader_720 import upgrade_720
from .upgrader_800 import upgrade_800
from .upgrader_810 import upgrade_810
from .upgrader_820 import upgrade_820
from .upgrader_830 import upgrade_830
from .upgrader_840 import upgrade_840
from .upgrader_850 import upgrade_850
from .upgrader_860 import upgrade_860
from .upgrader_870 import upgrade_870
from .upgrader_880 import upgrade_880

logger = logging.getLogger(__name__)


class UpgradeMethod(t.NamedTuple):
    """Raw study upgrade method (old version, new version, upgrade function)."""

    old: str
    new: str
    method: t.Callable[[Path], None]
    files: t.List[Path]


_GENERAL_DATA_PATH = Path("settings/generaldata.ini")

UPGRADE_METHODS = [
    UpgradeMethod("700", "710", upgrade_710, [_GENERAL_DATA_PATH]),
    UpgradeMethod("710", "720", upgrade_720, []),
    UpgradeMethod("720", "800", upgrade_800, [_GENERAL_DATA_PATH]),
    UpgradeMethod("800", "810", upgrade_810, [_GENERAL_DATA_PATH, Path("input")]),
    UpgradeMethod("810", "820", upgrade_820, [Path("input/links")]),
    UpgradeMethod("820", "830", upgrade_830, [_GENERAL_DATA_PATH, Path("input/areas")]),
    UpgradeMethod("830", "840", upgrade_840, [_GENERAL_DATA_PATH]),
    UpgradeMethod("840", "850", upgrade_850, [_GENERAL_DATA_PATH]),
    UpgradeMethod("850", "860", upgrade_860, [Path("input"), _GENERAL_DATA_PATH]),
    UpgradeMethod("860", "870", upgrade_870, [Path("input/thermal"), Path("input/bindingconstraints")]),
    UpgradeMethod("870", "880", upgrade_880, [Path("input/st-storage/clusters")]),
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
    with tempfile.TemporaryDirectory(suffix=".upgrade.tmp", prefix="~", dir=study_path.parent) as path:
        tmp_dir = Path(path)
        try:
            src_version = get_current_version(study_path)
            files_to_upgrade = can_upgrade_version(src_version, target_version)
            files_to_retrieve = _copies_only_necessary_files(files_to_upgrade, study_path, tmp_dir)
            _do_upgrade(tmp_dir, src_version, target_version)
        except (StudyValidationError, InvalidUpgrade) as e:
            logger.warning(str(e))
            raise
        except Exception as e:
            logger.error(f"Unhandled exception : {e}", exc_info=True)
            raise
        else:
            _replace_safely_original_files(files_to_retrieve, study_path, tmp_dir)


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


def can_upgrade_version(from_version: str, to_version: str) -> t.List[Path]:
    """
    Checks if upgrading from one version to another is possible.

    Args:
        from_version: The current version of the study.
        to_version: The target version of the study.

    Returns:
        If the upgrade is possible, the list of concerned folders and files

    Raises:
        InvalidUpgrade: If the upgrade is not possible.
    """
    list_versions = []
    if from_version == to_version:
        raise InvalidUpgrade(f"Your study is already in version '{to_version}'")

    sources = [u.old for u in UPGRADE_METHODS]
    if from_version not in sources:
        raise InvalidUpgrade(f"Version '{from_version}' unknown: possible versions are {', '.join(sources)}")

    targets = [u.new for u in UPGRADE_METHODS]
    if to_version not in targets:
        raise InvalidUpgrade(f"Version '{to_version}' unknown: possible versions are {', '.join(targets)}")

    files = [u.files for u in UPGRADE_METHODS]
    curr_version = from_version
    for src, dst, file in zip(sources, targets, files):
        if curr_version == src:
            for path in file:
                if path not in list_versions:
                    list_versions.append(path)
            curr_version = dst
        if curr_version == to_version:
            return list_versions

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


def _copies_only_necessary_files(files_to_upgrade: t.List[Path], study_path: Path, tmp_path: Path) -> t.List[Path]:
    """
    Copies files concerned by the version upgrader into a temporary directory.
    Args:
        study_path: Path to the study.
        tmp_path: Path to the temporary directory where the file modification will be performed.
        files_to_upgrade: List[Path]: List of the files and folders concerned by the upgrade.
    Returns:
        The list of files and folders that were really copied. It's the same as files_to_upgrade but
        without any children that has parents already in the list.
    """
    files_to_copy = _filters_out_children_files(files_to_upgrade)
    files_to_copy.append(Path("study.antares"))
    files_to_retrieve = []
    for path in files_to_copy:
        entire_path = study_path / path
        if not entire_path.exists():
            # This can happen when upgrading a study to v8.8.
            continue
        if entire_path.is_dir():
            if not (tmp_path / path).exists():
                shutil.copytree(entire_path, tmp_path / path, dirs_exist_ok=True)
                files_to_retrieve.append(path)
        elif len(path.parts) == 1:
            shutil.copy(entire_path, tmp_path / path)
            files_to_retrieve.append(path)
        else:
            parent_path = path.parent
            (tmp_path / parent_path).mkdir(parents=True, exist_ok=True)
            shutil.copy(entire_path, tmp_path / parent_path)
            files_to_retrieve.append(path)
    return files_to_retrieve


def _filters_out_children_files(files_to_upgrade: t.List[Path]) -> t.List[Path]:
    """
    Filters out children paths of "input" if "input" is already in the list.
    Args:
        files_to_upgrade: List[Path]: List of the files and folders concerned by the upgrade.
    Returns:
        The list of files filtered
    """
    is_input_in_files_to_upgrade = Path("input") in files_to_upgrade
    if is_input_in_files_to_upgrade:
        files_to_keep = [Path("input")]
        files_to_keep.extend(path for path in files_to_upgrade if "input" not in path.parts)
        return files_to_keep
    return files_to_upgrade


def _replace_safely_original_files(files_to_replace: t.List[Path], study_path: Path, tmp_path: Path) -> None:
    """
    Replace files/folders of the study that should be upgraded by their copy already upgraded in the tmp directory.
    It uses Path.rename() and an intermediary tmp directory to swap the folders safely.
    In the end, all tmp directories are removed.
    Args:
        study_path: Path to the study.
        tmp_path: Path to the temporary directory where the file modification will be performed.
        files_to_replace: List[Path]: List of files and folders that were really copied
        (cf. _copies_only_necessary_files's doc just above)
    """
    for k, path in enumerate(files_to_replace):
        backup_dir = Path(
            tempfile.mkdtemp(
                suffix=f".backup_{k}.tmp",
                prefix="~",
                dir=study_path.parent,
            )
        )
        backup_dir.rmdir()
        original_path = study_path / path
        original_path.rename(backup_dir)
        (tmp_path / path).rename(original_path)
        if backup_dir.is_dir():
            shutil.rmtree(backup_dir)
        else:
            backup_dir.unlink()


def _do_upgrade(study_path: Path, src_version: str, target_version: str) -> None:
    _update_study_antares_file(target_version, study_path)
    curr_version = src_version
    for old, new, method, _ in UPGRADE_METHODS:
        if curr_version == old and curr_version != target_version:
            method(study_path)
            curr_version = new


def should_study_be_denormalized(src_version: str, target_version: str) -> bool:
    try:
        can_upgrade_version(src_version, target_version)
    except InvalidUpgrade:
        return False
    curr_version = src_version
    list_of_upgrades = []
    for old, new, method, _ in UPGRADE_METHODS:
        if curr_version == old and curr_version != target_version:
            list_of_upgrades.append(new)
            curr_version = new
    # These upgrades alter matrices so the study needs to be denormalized
    return "820" in list_of_upgrades or "870" in list_of_upgrades
