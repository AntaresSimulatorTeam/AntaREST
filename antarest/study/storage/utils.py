# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
import logging
import math
import os
import re
import shutil
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, List, Optional, Sequence, cast
from uuid import uuid4
from zipfile import ZipFile

from antares.study.version import StudyVersion
from antares.study.version.create_app import CreateApp
from antares.study.version.upgrade_app import is_temporary_upgrade_dir

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
from antarest.core.model import PermissionInfo, StudyPermissionType
from antarest.core.permissions import check_permission
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.serde.ini_reader import IniReader
from antarest.core.serde.ini_writer import IniWriter
from antarest.core.utils.archives import is_archive_format
from antarest.core.utils.utils import StopWatch
from antarest.login.utils import require_current_user
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    STUDY_REFERENCE_TEMPLATES,
    STUDY_VERSION_9_0,
    MatrixIndex,
    Study,
    StudyDownloadLevelDTO,
    StudyMetadataDTO,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import Mode
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers

logger = logging.getLogger(__name__)


TS_GEN_PREFIX = "~"
TS_GEN_SUFFIX = ".thermal_timeseries_gen.tmp"


# noinspection SpellCheckingInspection
def update_antares_info(metadata: Study, study_tree: FileStudyTree, *, update_author: bool) -> None:
    study_data_info = study_tree.get(["study"])
    study_data_info["antares"]["caption"] = metadata.name
    study_data_info["antares"]["created"] = metadata.created_at.timestamp() if metadata.created_at is not None else "0"
    study_data_info["antares"]["lastsave"] = metadata.updated_at.timestamp() if metadata.updated_at is not None else "0"
    version = StudyVersion.parse(metadata.version)
    study_data_info["antares"]["version"] = f"{version:2d}" if version >= STUDY_VERSION_9_0 else f"{version:ddd}"
    if metadata.additional_data:
        study_data_info["antares"]["editor"] = metadata.additional_data.editor or metadata.additional_data.author
        if update_author:
            study_data_info["antares"]["author"] = metadata.additional_data.author
    study_tree.save(study_data_info, ["study"])


def fix_study_root(study_path: Path) -> None:
    """
    Fix possibly the wrong study root in zipped archive (when the study root is nested).

    Args:
        study_path: the study initial root path
    """
    # TODO: what if it is a zipped output ?
    if is_archive_format(study_path.suffix):
        return None

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


def extract_output_name(path_output: Path, new_suffix_name: Optional[str] = None) -> str:
    ini_reader = IniReader()
    archived = is_output_archived(path_output)
    if archived:
        temp_dir = tempfile.TemporaryDirectory()
        s = StopWatch()
        with ZipFile(path_output, "r") as zip_obj:
            zip_obj.extract("info.antares-output", temp_dir.name)
            info_antares_output = ini_reader.read(Path(temp_dir.name) / "info.antares-output")
        s.log_elapsed(lambda x: logger.info(f"info.antares_output has been read in {x}s"))
        temp_dir.cleanup()

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
            ini_writer = IniWriter()
            ini_writer.write(info_antares_output, path_output / "info.antares-output")
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


def create_new_empty_study(version: StudyVersion, path_study: Path) -> None:
    if version not in STUDY_REFERENCE_TEMPLATES:
        msg = f"{version} is not a supported version, supported versions are: {STUDY_REFERENCE_TEMPLATES}"
        raise UnsupportedStudyVersion(msg)

    app = CreateApp(study_dir=path_study, caption="To be replaced", version=version, author="Unknown")
    app()


def study_matcher(
    name: Optional[str], workspace: Optional[str], folder: Optional[str]
) -> Callable[[StudyMetadataDTO], bool]:
    def study_match(study: StudyMetadataDTO) -> bool:
        if name and not study.name.startswith(name):
            return False
        if workspace and study.workspace != workspace:
            return False
        if folder and (not study.folder or not study.folder.startswith(folder)):
            return False
        return True

    return study_match


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


def assert_permission(study: Optional[Study | StudyMetadataDTO], permission_type: StudyPermissionType) -> None:
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


def get_start_date(
    file_study: FileStudy,
    output_id: Optional[str] = None,
    level: StudyDownloadLevelDTO = StudyDownloadLevelDTO.HOURLY,
) -> MatrixIndex:
    """
    Retrieve the index (start date and step count) for output or input matrices

    Args:
        file_study: Study data
        output_id: id of the output, if None, then it's the start date of the input matrices
        level: granularity of the steps

    """
    config = FileStudyHelpers.get_config(file_study, output_id)["general"]
    starting_month = cast(str, config.get("first-month-in-year"))
    starting_day = cast(str, config.get("january.1st"))
    leapyear = cast(bool, config.get("leapyear"))
    first_week_day = cast(str, config.get("first.weekday"))
    start_offset = cast(int, config.get("simulation.start"))
    end = cast(int, config.get("simulation.end"))

    starting_month_index = MONTHS[starting_month.title()]
    starting_day_index = DAY_NAMES.index(starting_day.title())
    target_year = 2018
    while True:
        if leapyear == calendar.isleap(target_year + (starting_month_index > 2)):
            first_day = datetime(target_year + (starting_month_index != 1), 1, 1)
            if first_day.weekday() == starting_day_index:
                break
        target_year += 1

    start_offset_days = timedelta(days=(0 if output_id is None else start_offset - 1))
    start_date = datetime(target_year, starting_month_index, 1) + start_offset_days

    def _get_steps(
        daily_steps: int, temporality: StudyDownloadLevelDTO, begin_date: datetime, is_output: Optional[str] = None
    ) -> int:
        temporality_mapping = {
            StudyDownloadLevelDTO.DAILY: daily_steps,
            StudyDownloadLevelDTO.HOURLY: daily_steps * 24,
            StudyDownloadLevelDTO.ANNUAL: 1,
            StudyDownloadLevelDTO.WEEKLY: math.ceil(daily_steps / 7),
            StudyDownloadLevelDTO.MONTHLY: 12,
        }

        if temporality == StudyDownloadLevelDTO.MONTHLY and is_output:
            end_date = begin_date + timedelta(days=daily_steps)
            same_year = end_date.year == begin_date.year
            return 1 + end_date.month - begin_date.month if same_year else (13 - begin_date.month) + end_date.month

        return temporality_mapping[temporality]

    days_count = MATRIX_INPUT_DAYS_COUNT if output_id is None else end - start_offset + 1
    steps = _get_steps(days_count, level, start_date, output_id)

    first_week_day_index = DAY_NAMES.index(first_week_day)
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


def export_study_flat(
    study_dir: Path,
    dest: Path,
    study_factory: StudyFactory,
    outputs: bool = True,
    output_list_filter: Optional[List[str]] = None,
    denormalize: bool = True,
    output_src_path: Optional[Path] = None,
    is_study_managed: bool = True,
) -> None:
    start_time = time.time()

    output_src_path = output_src_path or study_dir / "output"
    output_dest_path = dest / "output"

    def ignore_outputs(directory: str, _: Sequence[str]) -> Sequence[str]:
        return ["output"] if str(directory) == str(study_dir) else []

    shutil.copytree(src=study_dir, dst=dest, ignore=ignore_outputs)

    if outputs and output_src_path.exists():
        if output_list_filter is None:
            # Retrieve all directories or ZIP files without duplicates
            output_list_filter = list(
                {f.with_suffix("").name for f in output_src_path.iterdir() if f.is_dir() or f.suffix == ".zip"}
            )
        # Copy each folder or uncompress each ZIP file to the destination dir.
        shutil.rmtree(output_dest_path, ignore_errors=True)
        output_dest_path.mkdir()
        for output in output_list_filter:
            zip_path = output_src_path / f"{output}.zip"
            if zip_path.exists():
                with ZipFile(zip_path) as zf:
                    zf.extractall(output_dest_path / output)
            else:
                shutil.copytree(
                    src=output_src_path / output,
                    dst=output_dest_path / output,
                )

    stop_time = time.time()
    duration = "{:.3f}".format(stop_time - start_time)
    with_outputs = "with outputs" if outputs else "without outputs"
    logger.info(f"Study '{study_dir}' exported ({with_outputs}, flat mode) in {duration}s")
    study = study_factory.create_from_fs(dest, is_study_managed, "", use_cache=False)
    if denormalize:
        study.tree.denormalize()
        duration = "{:.3f}".format(time.time() - stop_time)
        logger.info(f"Study '{study_dir}' denormalized in {duration}s")


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


def should_ignore_folder_for_scan(path: Path, filter_in: List[str], filter_out: List[str]) -> bool:
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


def has_children(path: Path, filter_in: List[str], filter_out: List[str], show_hidden_file: bool = False) -> bool:
    for sub_path in path.iterdir():
        try:
            show = show_hidden_file or not sub_path.name.startswith(".")
            if not should_ignore_folder_for_scan(sub_path, filter_in, filter_out) and show:
                return True
        except (PermissionError, OSError):
            logger.warning(f"tried to run is_non_study_folder on {sub_path} but no permission")
    return False


def is_non_study_folder(path: Path, filter_in: List[str], filter_out: List[str]) -> bool:
    if is_study_folder(path):
        return False
    if should_ignore_folder_for_scan(path, filter_in, filter_out):
        return False
    return True
