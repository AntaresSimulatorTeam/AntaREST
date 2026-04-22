# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import calendar
import contextlib
import logging
import math
import os
import re
import shutil
import time
from collections.abc import Sequence
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path, PurePosixPath
from typing import Any, cast
from uuid import uuid4
from zipfile import ZipFile

from antares.study.version import StudyVersion
from antares.study.version.create_app import CreateApp
from antares.study.version.upgrade_app import is_temporary_upgrade_dir
from pydantic import ConfigDict

from antarest.core.config import Config, WorkspaceConfig
from antarest.core.exceptions import (
    CannotAccessInternalWorkspace,
    FolderNotFoundInWorkspace,
    StudyValidationError,
    UnsupportedStudyVersion,
    WorkspaceNotFound,
)
from antarest.core.interfaces.cache import (
    ICache,
    study_config_cache_key,
    study_raw_cache_key,
)
from antarest.core.model import PermissionInfo, PublicMode, StudyPermissionType
from antarest.core.permissions import check_permission
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.ini_reader import IniReader
from antarest.core.serde.ini_writer import IniWriter
from antarest.core.utils.archives import is_archive_format
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.login.model import Group, Identity
from antarest.login.utils import get_user_impersonator, require_current_user
from antarest.study.business.model.config.general_model import GeneralConfig, Mode
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    STUDY_REFERENCE_TEMPLATES,
    MatrixFrequency,
    MatrixIndex,
    RawStudy,
    Study,
    StudyFolder,
    StudyMetadataDTO,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers

logger = logging.getLogger(__name__)


TS_GEN_PREFIX = "~"
TS_GEN_SUFFIX = ".thermal_timeseries_gen.tmp"


def update_antares_info(metadata: Study, study_tree: FileStudyTree, update_author: bool) -> None:
    """
    Update antares study information in the study.antares file.

    Args:
        metadata: Study metadata containing name, dates, etc.
        study_tree: File study tree to update
        update_author: Whether to update the author field
    """
    study_data_info = study_tree.get(["study"])
    antares_info = study_data_info["antares"]

    author = metadata.author
    editor = metadata.editor

    # Update basic fields
    antares_info["caption"] = metadata.name
    antares_info["created"] = format_timestamp(metadata.created_at)
    antares_info["lastsave"] = format_timestamp(metadata.updated_at)
    antares_info["editor"] = editor

    # Update author-related fields if additional_data exists
    if update_author:
        antares_info["author"] = author

    study_tree.save(study_data_info, ["study"])


def format_timestamp(dt: datetime | None) -> float:
    """Format datetime as a timestamp float or 0 if None."""
    return dt.timestamp() if dt is not None else 0


def fix_study_root(study_path: Path) -> None:
    """
    Fix possibly the wrong study root in zipped archive (when the study root is nested).

    Args:
        study_path: the study initial root path
    """
    if not study_path.is_dir():
        raise StudyValidationError("Not a directory: '{study_path}'")

    root_path = study_path
    contents = os.listdir(root_path)
    sub_root_path = None
    while len(contents) == 1 and (root_path / contents[0]).is_dir():
        new_root = root_path / contents[0]
        if sub_root_path is None:
            sub_root_path = root_path / str(uuid4())
            shutil.move(str(new_root), str(sub_root_path))
            new_root = sub_root_path

        logger.debug(f"Searching study root in {new_root}")
        root_path = new_root
        if not new_root.is_dir():
            raise StudyValidationError("Not a directory: '{new_root}'")
        contents = os.listdir(new_root)

    if sub_root_path is not None:
        for item in os.listdir(root_path):
            shutil.move(str(root_path / item), str(study_path))
        shutil.rmtree(sub_root_path)


def find_single_output_path(all_output_path: Path) -> Path:
    children = os.listdir(all_output_path)
    if len(children) == 1:
        if children[0].endswith(".zip"):
            return all_output_path / children[0]
        return find_single_output_path(all_output_path / children[0])
    return all_output_path


def is_output_archived(path_output: Path) -> bool:
    # Returns True it the given path is archived or if adding a suffix to the path points to an existing path
    suffixes = [".zip"]
    if path_output.suffixes and path_output.suffixes[-1] in suffixes:
        return True
    return any((path_output.parent / (path_output.name + suffix)).exists() for suffix in suffixes)


def extract_output_name(path_output: Path, new_suffix_name: str | None = None) -> str:
    """
    Constructs the full output name such as "20201014-1422eco-hello" from the info.antares-output file content.

    If new_suffix_name is provided, replaces the part suffix part ("hello" in the example) with that new suffix,
    and updates the file so that it's consistent with that new suffix.

    Warning: the update part will not work for zip files, which don't allow in place updates.
    """
    ini_reader = IniReader()
    archived = is_output_archived(path_output)
    if archived:
        with ZipFile(path_output, "r") as zip_obj:
            content = zip_obj.read("info.antares-output")
            info_antares_output = ini_reader.read(StringIO(content.decode("utf-8")))
    else:
        info_antares_output = ini_reader.read(path_output / "info.antares-output")

    general_info = info_antares_output["general"]

    date = datetime.fromtimestamp(int(general_info["timestamp"])).strftime("%Y%m%d-%H%M")

    mode = Mode(general_info["mode"]).get_output_suffix()

    suffix_name = general_info["name"] or ""
    if new_suffix_name:
        suffix_name = new_suffix_name
        general_info["name"] = suffix_name
        if not archived:
            IniWriter().write(info_antares_output, path_output / "info.antares-output")
        else:
            logger.warning("Could not rewrite the new name inside the output: the output is archived")

    name = f"-{suffix_name}" if suffix_name else ""
    return f"{date}{mode}{name}"


def is_managed(study: Study) -> bool:
    return not hasattr(study, "workspace") or study.workspace == DEFAULT_WORKSPACE_NAME


def remove_from_cache(cache: ICache, root_id: str) -> None:
    cache.invalidate_all(
        [
            study_raw_cache_key(root_id),
            study_config_cache_key(root_id),
        ]
    )


def create_new_empty_study(
    version: StudyVersion, path_study: Path, name: str = "To be replaced", author: str = "Unknown"
) -> None:
    if version not in STUDY_REFERENCE_TEMPLATES:
        msg = f"{version} is not a supported version, supported versions are: {STUDY_REFERENCE_TEMPLATES}"
        raise UnsupportedStudyVersion(msg)

    app = CreateApp(study_dir=path_study, caption=name, version=version, author=author)
    app()


def assert_permission_on_studies(
    studies: Sequence[Study | StudyMetadataDTO], permission_type: StudyPermissionType
) -> None:
    """
    Asserts whether the provided user has the required permissions on the given studies.

    Args:
        studies: The studies for which permissions need to be verified.
        permission_type: The type of permission to be checked for the user.

    Returns:
        `True` if the user has the required permissions, `False` otherwise.

    Raises:
        `UserHasNotPermissionError`: If the raising parameter is set to `True`
            and the user does not have the required permissions.
    """
    user = require_current_user()
    msg = {
        0: f"FAIL permissions: user '{user}' has no access to any study",
        1: f"FAIL permissions: user '{user}' does not have {permission_type.value} permission on {studies[0].id}",
        2: f"FAIL permissions: user '{user}' does not have {permission_type.value} permission on all studies",
    }[min(len(studies), 2)]
    infos = (PermissionInfo.from_study(study) for study in studies)
    if any(not check_permission(user, permission_info, permission_type) for permission_info in infos):
        logger.error(msg)
        raise UserHasNotPermissionError(msg)


def assert_permission(study: Study | StudyMetadataDTO | None, permission_type: StudyPermissionType) -> None:
    """
    Assert user has permission to edit or read study.

    Args:
        study: study asked
        permission_type: level of permission

    Returns:
        `True` if the user has the required permissions, `False` otherwise.

    Raises:
        `UserHasNotPermissionError`: If the raising parameter is set to `True`
            and the user does not have the required permissions.
    """
    studies = [study] if study else []
    assert_permission_on_studies(studies, permission_type)


MATRIX_INPUT_DAYS_COUNT = 365

MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class SimulationRangeDefinition(AntaresBaseModel):
    """
    Definition of the time range for a simulation.

    Together, the starting month, january 1st and leapyear define the 12-months target range.
    Then the actually simulated range may be reduced with simulation_start and simulation_end
    parameters, which define the first and last day to be simulated in that 12-months range.
    first_weekday is only used for weekly aggregation of data in the output, it defines on which
    day the week starts.

    Attributes:
        starting_month: index of the month in which the simulation starts (1-12)
        january_1st_weekday: weekday of january 1st in the simulated year
        leap_year: whether the simulated year is a leap year
        start_day: first day of the actual simulated range inside the 12-months range
        end_day: last day of the actual simulated range inside the 12-months range
        first_weekday: only used to determine where weeks should be "cut", when computing weekly aggregates.
    """

    model_config = ConfigDict(populate_by_name=True)

    # together, those parameters define the 12-months range
    starting_month: int
    january_1st_weekday: int
    leap_year: bool

    # possible reduction of simulated range
    start_day: int
    end_day: int

    # defines where weeks are "cut" in weekly aggregation of outputs
    first_weekday: int


def parse_simulation_range(config: dict[str, Any]) -> SimulationRangeDefinition:
    """
    Parses a dictionary as defined in the "general" section of generaldata.ini or parameters.ini
    """

    starting_month = cast(str, config.get("first-month-in-year"))
    starting_day = cast(str, config.get("january.1st"))
    leapyear = cast(bool, config.get("leapyear"))
    first_week_day = cast(str, config.get("first.weekday"))
    simulation_start = cast(int, config.get("simulation.start"))
    simulation_end = cast(int, config.get("simulation.end"))

    starting_month_index = MONTHS[starting_month.title()]
    starting_day_index = DAY_NAMES.index(starting_day.title())
    first_week_day_index = DAY_NAMES.index(first_week_day)

    return SimulationRangeDefinition(
        starting_month=starting_month_index,
        january_1st_weekday=starting_day_index,
        leap_year=leapyear,
        start_day=simulation_start,
        end_day=simulation_end,
        first_weekday=first_week_day_index,
    )


def extract_simulation_range_from_model(general: GeneralConfig) -> SimulationRangeDefinition:
    starting_month = general.first_month
    starting_day = general.first_january
    leapyear = general.leap_year
    first_week_day = general.first_week_day
    simulation_start = general.first_day
    simulation_end = general.last_day

    starting_month_index = MONTHS[starting_month.title()]
    starting_day_index = DAY_NAMES.index(starting_day.title())
    first_week_day_index = DAY_NAMES.index(first_week_day)

    return SimulationRangeDefinition(
        starting_month=starting_month_index,
        january_1st_weekday=starting_day_index,
        leap_year=leapyear,
        start_day=simulation_start,
        end_day=simulation_end,
        first_weekday=first_week_day_index,
    )


def get_matrix_index(
    simulation_range: SimulationRangeDefinition,
    is_output: bool,
    level: MatrixFrequency,
) -> MatrixIndex:
    """
    Retrieve the index (start date and step count) for output or input matrices

    Args:
        file_study: Study data
        output_id: id of the output, if None, then it's the start date of the input matrices
        level: granularity of the steps

    """
    starting_month_index = simulation_range.starting_month
    starting_day_index = simulation_range.january_1st_weekday
    leapyear = simulation_range.leap_year
    first_week_day_index = simulation_range.first_weekday
    start_offset = simulation_range.start_day
    end = simulation_range.end_day

    target_year = 2018
    while True:
        if leapyear == calendar.isleap(target_year + (starting_month_index > 2)):
            first_day = datetime(target_year + (starting_month_index != 1), 1, 1)
            if first_day.weekday() == starting_day_index:
                break
        target_year += 1

    start_offset_days = timedelta(days=(0 if not is_output else start_offset - 1))
    start_date = datetime(target_year, starting_month_index, 1) + start_offset_days

    def _get_steps(daily_steps: int, temporality: MatrixFrequency, begin_date: datetime, is_output: bool) -> int:
        temporality_mapping = {
            MatrixFrequency.DAILY: daily_steps,
            MatrixFrequency.HOURLY: daily_steps * 24,
            MatrixFrequency.ANNUAL: 1,
            MatrixFrequency.WEEKLY: math.ceil(daily_steps / 7),
            MatrixFrequency.MONTHLY: 12,
        }

        if temporality == MatrixFrequency.MONTHLY and is_output:
            end_date = begin_date + timedelta(days=daily_steps)
            same_year = end_date.year == begin_date.year
            return 1 + end_date.month - begin_date.month if same_year else (13 - begin_date.month) + end_date.month

        return temporality_mapping[temporality]

    days_count = MATRIX_INPUT_DAYS_COUNT if not is_output else end - start_offset + 1
    steps = _get_steps(days_count, level, start_date, is_output)

    first_week_offset = 0
    for first_week_offset in range(7):
        first_day = start_date + timedelta(days=first_week_offset)
        if first_day.weekday() == first_week_day_index:
            break
    first_week_size = first_week_offset if first_week_offset != 0 else 7

    return MatrixIndex.model_construct(
        start_date=str(start_date),
        steps=steps,
        first_week_size=first_week_size,
        level=level,
    )


def get_start_date(
    file_study: FileStudy,
    output_id: str | None = None,
    level: MatrixFrequency = MatrixFrequency.HOURLY,
) -> MatrixIndex:
    """
    Retrieve the index (start date and step count) for output or input matrices

    Args:
        file_study: Study data
        output_id: id of the output, if None, then it's the start date of the input matrices
        level: granularity of the steps

    """
    config = FileStudyHelpers.get_config(file_study, output_id)["general"]
    simulation_range = parse_simulation_range(config)
    return get_matrix_index(simulation_range, output_id is not None, level)


def is_folder_safe(workspace: WorkspaceConfig, folder: str) -> bool:
    """
    Check if the provided folder path is safe to prevent path traversal attack.

    Args:
        workspace: The workspace name.
        folder: The folder path.

    Returns:
        `True` if the folder path is safe, `False` otherwise.
    """
    requested_path = workspace.path / folder
    requested_path = requested_path.resolve()
    safe_dir = workspace.path.resolve()
    # check whether the requested path is a subdirectory of the workspace
    return requested_path.is_relative_to(safe_dir)


def is_study_folder(path: Path) -> bool:
    return path.is_dir() and (path / "study.antares").exists()


def is_aw_no_scan(path: Path) -> bool:
    return (path / "AW_NO_SCAN").exists()


def get_workspace_from_config(config: Config, workspace_name: str, default_allowed: bool = False) -> WorkspaceConfig:
    if not default_allowed and workspace_name == DEFAULT_WORKSPACE_NAME:
        raise CannotAccessInternalWorkspace()
    try:
        return config.storage.workspaces[workspace_name]
    except KeyError:
        logger.error(f"Workspace {workspace_name} not found")
        raise WorkspaceNotFound(f"Workspace {workspace_name} not found")


def get_folder_from_workspace(workspace: WorkspaceConfig, folder: str) -> Path:
    if not is_folder_safe(workspace, folder):
        raise FolderNotFoundInWorkspace(f"Invalid path for folder: {folder} in workspace {workspace}")
    folder_path = workspace.path / folder
    if not folder_path.is_dir():
        raise FolderNotFoundInWorkspace(f"Provided path is not dir: {folder} in workspace {workspace}")
    return folder_path


def is_ts_gen_tmp_dir(path: Path) -> bool:
    """
    Check if a path is a temporary directory used for thermal timeseries generation
    Args:
        path: the path to check

    Returns:
        True if the path is a temporary directory used for thermal timeseries generation
    """
    return path.name.startswith(TS_GEN_PREFIX) and "".join(path.suffixes[-2:]) == TS_GEN_SUFFIX and path.is_dir()


def should_ignore_folder_for_scan(path: Path, filter_in: list[str], filter_out: list[str]) -> bool:
    if is_aw_no_scan(path):
        logger.info(f"No scan directive file found. Will skip further scan of folder {path}")
        return True

    if is_temporary_upgrade_dir(path):
        logger.info(f"Upgrade temporary folder found. Will skip further scan of folder {path}")
        return True

    if is_ts_gen_tmp_dir(path):
        logger.info(f"TS generation temporary folder found. Will skip further scan of folder {path}")
        return True

    return not (
        path.is_dir()
        and any(re.search(regex, path.name) for regex in filter_in)
        and not any(re.search(regex, path.name) for regex in filter_out)
    )


def has_children(path: Path, filter_in: list[str], filter_out: list[str], show_hidden_file: bool = False) -> bool:
    for sub_path in path.iterdir():
        try:
            show = show_hidden_file or not sub_path.name.startswith(".")
            if not should_ignore_folder_for_scan(sub_path, filter_in, filter_out) and show:
                return True
        except (PermissionError, OSError):
            logger.warning(f"tried to run is_non_study_folder on {sub_path} but no permission")
    return False


def rec_scan_for_studies(
    path: Path,
    workspace: str,
    groups: list[Group],
    filter_in: list[str],
    filter_out: list[str],
    max_depth: int | None = None,
) -> list[StudyFolder]:
    """
    Recursively scan a directory for studies.

    A study is identified by the presence of a "study.antares" file.

    Args:
        path: The directory path to scan.
        workspace: The workspace name.
        groups: The groups to associate with found studies.
        filter_in: Regex patterns for folders to include.
        filter_out: Regex patterns for folders to exclude.
        max_depth: Maximum depth to scan. None means unlimited.

    Returns:
        A list of StudyFolder objects representing found studies.
    """
    try:
        if should_ignore_folder_for_scan(path, filter_in, filter_out):
            return []

        if (path / "study.antares").exists():
            logger.debug(f"Study {path.name} found in {workspace}")
            return [StudyFolder(path, workspace, groups)]

        if max_depth is not None and max_depth <= 0:
            logger.info(f"Scan was configured to not go any deeper, max_depth: {max_depth}")
            return []

        folders: list[StudyFolder] = []
        if path.is_dir():
            for child in path.iterdir():
                child_max_depth = max_depth - 1 if max_depth is not None else None
                try:
                    folders += rec_scan_for_studies(child, workspace, groups, filter_in, filter_out, child_max_depth)
                except Exception as e:
                    logger.error(f"Failed to scan dir {child}", exc_info=e)
        return folders
    except Exception as e:
        logger.error(f"Failed to scan dir {path}", exc_info=e)
        return []


def get_disk_usage(path: Path) -> int:
    """Calculate the total disk usage (in bytes) of a study in a compressed file or directory."""
    if is_archive_format(path.suffix.lower()):
        return os.path.getsize(path)
    total_size = 0
    with contextlib.suppress(FileNotFoundError, PermissionError):
        with os.scandir(path) as it:
            for entry in it:
                with contextlib.suppress(FileNotFoundError, PermissionError):
                    if entry.is_file():
                        total_size += entry.stat().st_size
                    elif entry.is_dir():
                        total_size += get_disk_usage(path=Path(entry.path))
    return total_size


def get_user_name_from_id(user_id: int) -> str:
    """
    Utility method that retrieves a user's name based on their id.
    Args:
        user_id: user id (user must exist)
    Returns: String representing the user's name
    """
    user_obj: Identity | None = db.session.get(Identity, user_id)
    if user_obj is None:
        return "Unnamed"
    return str(user_obj.name)


def get_current_user_name() -> str:
    return get_user_name_from_id(get_user_impersonator())


def export_study_to_flat_directory(study_dir: Path, dest: Path) -> None:
    start_time = time.time()

    def ignore_outputs(directory: str, _: Sequence[str]) -> Sequence[str]:
        return ["output"] if str(directory) == str(study_dir) else []

    shutil.copytree(src=study_dir, dst=dest, ignore=ignore_outputs)

    stop_time = time.time()
    duration = f"{stop_time - start_time:.3f}"
    logger.info(f"Study '{study_dir}' exported (flat mode) in {duration}s")


def build_raw_study_from_source(
    name: str, path: Path, groups: list[str], src_study: Study, destination_folder: PurePosixPath
) -> RawStudy:
    dest_id = str(uuid4())
    now_utc = current_time()
    dest_study = RawStudy(
        id=dest_id,
        name=name,
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(path / dest_id),
        created_at=now_utc,
        updated_at=now_utc,
        version=src_study.version,
        author=src_study.author,
        editor=get_current_user_name(),
        horizon=src_study.horizon,
        public_mode=PublicMode.NONE if groups else PublicMode.READ,
        groups=groups,
        folder=str(destination_folder / dest_id),
        storage_mode=src_study.storage_mode,
    )
    return dest_study
