import glob
import logging
import re
import shutil
import tempfile
import time
from http import HTTPStatus
from http.client import HTTPException
from pathlib import Path
from typing import Callable, NamedTuple, cast

import numpy
import pandas  # type: ignore

from antarest.core.exceptions import (
    StudyValidationError,
    UnsupportedStudyVersion,
)
from antarest.study.storage.antares_configparser import (
    AntaresConfigParser,
    AntaresSectionProxy,
)

LOGGER = logging.getLogger(__name__)
OTHER_PREFERENCES = "other preferences"
GENERAL_DATA_PATH = Path("settings") / "generaldata.ini"
ADEQUACY_PATCH = "adequacy patch"
MAPPING_TRANSMISSION_CAPACITIES = {
    True: "local-values",
    False: "null-for-all-links",
    "infinite": "infinite-for-all-links",
}


def upgrade_710(study_path: Path) -> None:
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


def upgrade_720(study_path: Path) -> None:
    # There is no input modification between the 7.1.0 and the 7.2.0 version
    pass


def upgrade_800(study_path: Path) -> None:
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


def upgrade_810(study_path: Path) -> None:
    config = AntaresConfigParser()
    config.read(study_path / GENERAL_DATA_PATH)
    config[OTHER_PREFERENCES]["renewable-generation-modelling"] = "aggregated"
    with open(study_path / GENERAL_DATA_PATH, "w") as configfile:
        config.write(configfile)
    study_path.joinpath("input", "renewables", "clusters").mkdir(parents=True)
    study_path.joinpath("input", "renewables", "series").mkdir(parents=True)

    # TODO Cannot update study with renewables clusters for the moment


def upgrade_820(study_path: Path) -> None:
    links = glob.glob(str(study_path / "input" / "links" / "*"))
    if len(links) > 0:
        for folder in links:
            folder_path = Path(folder)
            all_txt = glob.glob(str(folder_path / "*.txt"))
            if len(all_txt) > 0:
                (folder_path / "capacities").mkdir()
                for txt in all_txt:
                    df = pandas.read_csv(txt, sep="\t", header=None)
                    df_parameters = df.iloc[:, 2:8]
                    df_direct = df.iloc[:, 0]
                    df_indirect = df.iloc[:, 1]
                    name = Path(txt).stem
                    numpy.savetxt(
                        folder_path / f"{name}_parameters.txt",
                        df_parameters.values,
                        delimiter="\t",
                        fmt="%.6f",
                    )
                    numpy.savetxt(
                        folder_path / "capacities" / f"{name}_direct.txt",
                        df_direct.values,
                        delimiter="\t",
                        fmt="%.6f",
                    )
                    numpy.savetxt(
                        folder_path / "capacities" / f"{name}_indirect.txt",
                        df_indirect.values,
                        delimiter="\t",
                        fmt="%.6f",
                    )
                    (folder_path / f"{name}.txt").unlink()


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


def upgrade_840(study_path: Path) -> None:
    config = AntaresConfigParser()
    config.read(study_path / GENERAL_DATA_PATH)
    config["optimization"][
        "transmission-capacities"
    ] = MAPPING_TRANSMISSION_CAPACITIES[
        config["optimization"].getboolean("transmission-capacities")
    ]
    config.remove_option("optimization", "include-split-exported-mps")
    with open(study_path / GENERAL_DATA_PATH, "w") as configfile:
        config.write(configfile)


def upgrade_850(study_path: Path) -> None:
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


class InvalidUpgrade(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


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
        do_upgrade(tmp_dir, src_version, target_version)
    except (StudyValidationError, InvalidUpgrade) as e:
        shutil.rmtree(tmp_dir)
        LOGGER.warning(str(e))
        raise
    except UnsupportedStudyVersion as e:
        shutil.rmtree(tmp_dir)
        LOGGER.warning(str(e.detail))
        raise
    except Exception as e:
        shutil.rmtree(tmp_dir)
        LOGGER.error(f"Unhandled exception : {e}", exc_info=True)
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


def update_study_antares_file(target_version: str, study_path: Path) -> None:
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


def do_upgrade(
    study_path: Path, src_version: str, target_version: str
) -> None:
    update_study_antares_file(target_version, study_path)
    curr_version = src_version
    for old, new, method in UPGRADE_METHODS:
        if curr_version == old and curr_version != target_version:
            method(study_path)
            curr_version = new
