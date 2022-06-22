import calendar
import logging
import os
import shutil
import tempfile
from datetime import timedelta, datetime
from math import ceil
from pathlib import Path
from time import strptime
from typing import Optional, Union, cast, Callable, Tuple, Any
from uuid import uuid4
from zipfile import ZipFile

from antarest.core.config import Config
from antarest.core.exceptions import (
    StudyValidationError,
    UnsupportedStudyVersion,
)
from antarest.core.interfaces.cache import CacheConstants, ICache
from antarest.core.jwt import JWTUser
from antarest.core.model import PermissionInfo, StudyPermissionType, PublicMode
from antarest.core.permissions import check_permission
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.utils.utils import StopWatch
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    Study,
    STUDY_REFERENCE_TEMPLATES,
    StudyMetadataDTO,
    MatrixIndex,
    StudyDownloadLevelDTO,
)
from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers

logger = logging.getLogger(__name__)


def get_workspace_path(config: Config, workspace: str) -> Path:
    """
    Retrieve workspace path from config

    Args:
        workspace: workspace name
        config: antarest config
    Returns: path

    """
    return config.storage.workspaces[workspace].path


def get_default_workspace_path(config: Config) -> Path:
    """
    Get path of default workspace
    Returns: path

    """
    return get_workspace_path(config, DEFAULT_WORKSPACE_NAME)


def update_antares_info(metadata: Study, studytree: FileStudyTree) -> None:
    """
    Update study.antares data
    Args:
        metadata: study information
        studytree: study tree

    Returns: none, update is directly apply on study_data

    """
    study_data_info = studytree.get(["study"])
    study_data_info["antares"]["caption"] = metadata.name
    study_data_info["antares"]["created"] = metadata.created_at.timestamp()
    study_data_info["antares"]["lastsave"] = metadata.updated_at.timestamp()
    study_data_info["antares"]["version"] = metadata.version
    studytree.save(study_data_info, ["study"])


def fix_study_root(study_path: Path) -> None:
    """
    Fix possibly the wrong study root in zipped archive (when the study root is nested)

    @param study_path the study initial root path
    """
    # TODO: what if it is a zipped output ?
    if study_path.suffix == ".zip":
        return None

    if not study_path.is_dir():
        raise StudyValidationError("Not a directory")

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
            raise StudyValidationError("Not a directory")
        contents = os.listdir(new_root)

    if sub_root_path is not None:
        for item in os.listdir(root_path):
            shutil.move(str(root_path / item), str(study_path))
        shutil.rmtree(sub_root_path)


def find_single_output_path(all_output_path: Path) -> Path:
    children = os.listdir(all_output_path)
    if len(children) == 1:
        return find_single_output_path(all_output_path / children[0])
    return all_output_path


def extract_output_name(
    path_output: Path, new_suffix_name: Optional[str] = None
) -> str:
    ini_reader = IniReader()
    is_output_archived = path_output.suffix == ".zip"
    if is_output_archived:
        temp_dir = tempfile.TemporaryDirectory()
        s = StopWatch()
        with ZipFile(path_output, "r") as zip_obj:
            zip_obj.extract("info.antares-output", temp_dir.name)
            info_antares_output = ini_reader.read(
                Path(temp_dir.name) / "info.antares-output"
            )
        s.log_elapsed(
            lambda x: logger.info(f"info.antares_output has been read in {x}s")
        )
        temp_dir.cleanup()

    else:
        info_antares_output = ini_reader.read(
            path_output / "info.antares-output"
        )

    general_info = info_antares_output["general"]

    date = datetime.fromtimestamp(int(general_info["timestamp"])).strftime(
        "%Y%m%d-%H%M"
    )

    mode = "eco" if general_info["mode"] == "Economy" else "adq"
    suffix_name = general_info["name"] if general_info["name"] else ""
    if new_suffix_name:
        suffix_name = new_suffix_name
        general_info["name"] = suffix_name
        if not is_output_archived:
            ini_writer = IniWriter()
            ini_writer.write(
                info_antares_output, path_output / "info.antares-output"
            )
        else:
            logger.warning(
                "Could not rewrite the new name inside the output: the output is archived"
            )

    name = f"-{suffix_name}" if suffix_name else ""
    return f"{date}{mode}{name}"


def is_managed(study: Study) -> bool:
    return (
        not hasattr(study, "workspace")
        or study.workspace == DEFAULT_WORKSPACE_NAME
    )


def remove_from_cache(cache: ICache, root_id: str) -> None:
    cache.invalidate_all(
        [
            f"{CacheConstants.RAW_STUDY}/{root_id}",
            f"{CacheConstants.STUDY_FACTORY}/{root_id}",
        ]
    )


def create_new_empty_study(
    version: str, path_study: Path, path_resources: Path
) -> None:
    version_template: Optional[str] = STUDY_REFERENCE_TEMPLATES.get(
        version, None
    )
    if version_template is None:
        raise UnsupportedStudyVersion(version)

    empty_study_zip = path_resources / version_template

    with ZipFile(empty_study_zip) as zip_output:
        zip_output.extractall(path=path_study)


def create_permission_from_study(
    study: Union[Study, StudyMetadataDTO]
) -> PermissionInfo:
    return PermissionInfo(
        owner=study.owner.id if study.owner is not None else None,
        groups=[g.id for g in study.groups if g.id is not None],
        public_mode=PublicMode(study.public_mode)
        if study.public_mode is not None
        else PublicMode.NONE,
    )


def study_matcher(
    name: Optional[str], workspace: Optional[str], folder: Optional[str]
) -> Callable[[StudyMetadataDTO], bool]:
    def study_match(study: StudyMetadataDTO) -> bool:
        if name and not study.name.startswith(name):
            return False
        if workspace and study.workspace != workspace:
            return False
        if folder and (
            not study.folder or not study.folder.startswith(folder)
        ):
            return False
        return True

    return study_match


def assert_permission(
    user: Optional[JWTUser],
    study: Optional[Union[Study, StudyMetadataDTO]],
    permission_type: StudyPermissionType,
    raising: bool = True,
) -> bool:
    """
    Assert user has permission to edit or read study.
    Args:
        user: user logged
        study: study asked
        permission_type: level of permission
        raising: raise error if permission not matched

    Returns: true if permission match, false if not raising.

    """
    if not user:
        logger.error("FAIL permission: user is not logged")
        raise UserHasNotPermissionError()

    if not study:
        logger.error("FAIL permission: study not exist")
        raise ValueError("Metadata is None")

    permission_info = create_permission_from_study(study)
    ok = check_permission(user, permission_info, permission_type)
    if raising and not ok:
        logger.error(
            "FAIL permission: user %d has no permission on study %s",
            user.id,
            study.id,
        )
        raise UserHasNotPermissionError()

    return ok


MATRIX_INPUT_DAYS_COUNT = 365


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

    starting_month_index = strptime(starting_month, "%B").tm_mon
    target_year = 2000
    while True:
        if leapyear == calendar.isleap(target_year):
            first_day = datetime(target_year, starting_month_index, 1)
            if first_day.strftime("%A") == starting_day:
                break
        target_year += 1

    start_offset_days = (
        timedelta(days=start_offset - 1)
        if output_id is not None
        else timedelta(days=0)
    )
    start_date = (
        datetime(target_year, starting_month_index, 1) + start_offset_days
    )
    # base case is DAILY
    steps = (
        end - start_offset + 1
        if output_id is not None
        else MATRIX_INPUT_DAYS_COUNT
    )
    if level == StudyDownloadLevelDTO.HOURLY:
        steps = steps * 24
    elif level == StudyDownloadLevelDTO.ANNUAL:
        steps = 1
    elif level == StudyDownloadLevelDTO.WEEKLY:
        steps = ceil(steps / 7)
    elif level == StudyDownloadLevelDTO.MONTHLY:
        end_date = start_date + timedelta(days=steps)
        same_year = end_date.year == start_date.year
        if same_year:
            steps = 1 + end_date.month - start_date.month
        else:
            steps = (13 - start_date.month) + end_date.month

    first_week_offset = 0
    while True:
        if (start_date + timedelta(days=first_week_offset)).strftime(
            "%A"
        ) == first_week_day:
            break
        first_week_offset += 1
    first_week_size = first_week_offset if first_week_offset != 0 else 7

    return MatrixIndex.construct(
        start_date=str(start_date),
        steps=steps,
        first_week_size=first_week_size,
        level=level,
    )


def extract_file_to_tmp_dir(
    zip_path: Path, inside_zip_path: Path
) -> Tuple[Path, Any]:
    str_inside_zip_path = str(inside_zip_path)
    str_inside_zip_path.replace("\\", "/")
    tmp_dir = tempfile.TemporaryDirectory()
    with ZipFile(zip_path) as zip_obj:
        zip_obj.extract(str_inside_zip_path, tmp_dir.name)
    path = Path(tmp_dir.name) / inside_zip_path
    return path, tmp_dir
