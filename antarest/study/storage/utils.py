import calendar
import logging
import math
import os
import shutil
import tempfile
import time
import typing as t
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

from antarest.core.exceptions import StudyValidationError, UnsupportedStudyVersion
from antarest.core.interfaces.cache import CacheConstants, ICache
from antarest.core.jwt import JWTUser
from antarest.core.model import PermissionInfo, StudyPermissionType
from antarest.core.permissions import check_permission
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.utils.utils import StopWatch
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    STUDY_REFERENCE_TEMPLATES,
    MatrixIndex,
    Study,
    StudyDownloadLevelDTO,
    StudyMetadataDTO,
)
from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers

logger = logging.getLogger(__name__)


# noinspection SpellCheckingInspection
def update_antares_info(metadata: Study, study_tree: FileStudyTree, *, update_author: bool) -> None:
    """
    Update the "antares" information directly in the study tree.

    Args:
        metadata: The study object extracted from the database.
        study_tree: The study tree object.
        update_author: Specifies whether the author should be modified or not.
            The author's name should be updated when the study is created,
            but it is not changed if the study is copied.
    """
    study_data_info = study_tree.get(["study"])
    study_data_info["antares"]["caption"] = metadata.name
    study_data_info["antares"]["created"] = metadata.created_at.timestamp()
    study_data_info["antares"]["lastsave"] = metadata.updated_at.timestamp()
    study_data_info["antares"]["version"] = metadata.version
    if update_author and metadata.additional_data:
        study_data_info["antares"]["author"] = metadata.additional_data.author
    study_tree.save(study_data_info, ["study"])


def fix_study_root(study_path: Path) -> None:
    """
    Fix possibly the wrong study root in zipped archive (when the study root is nested).

    Args:
        study_path: the study initial root path
    """
    # TODO: what if it is a zipped output ?
    if study_path.suffix == ".zip":
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


def retrieve_output_path(job_path: Path) -> Path:
    output_already_zipped_path = job_path.with_suffix(".zip")
    if output_already_zipped_path.exists():
        return output_already_zipped_path

    output_inside_study = job_path / "output"
    if output_inside_study.is_dir():
        output_folders = os.listdir(output_inside_study)
        if len(output_folders) == 1:
            return output_inside_study / output_folders[0]

    return Path()


def extract_output_name(path_output: Path, new_suffix_name: t.Optional[str] = None) -> str:
    ini_reader = IniReader()
    is_output_archived = path_output.suffix == ".zip"
    if is_output_archived:
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

    mode = "eco" if general_info["mode"] == "Economy" else "adq"
    suffix_name = general_info["name"] or ""
    if new_suffix_name:
        suffix_name = new_suffix_name
        general_info["name"] = suffix_name
        if not is_output_archived:
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
            f"{CacheConstants.RAW_STUDY}/{root_id}",
            f"{CacheConstants.STUDY_FACTORY}/{root_id}",
        ]
    )


def create_new_empty_study(version: str, path_study: Path, path_resources: Path) -> None:
    version_template: t.Optional[str] = STUDY_REFERENCE_TEMPLATES.get(version, None)
    if version_template is None:
        raise UnsupportedStudyVersion(version)

    empty_study_zip = path_resources / version_template

    with ZipFile(empty_study_zip) as zip_output:
        zip_output.extractall(path=path_study)


def study_matcher(
    name: t.Optional[str], workspace: t.Optional[str], folder: t.Optional[str]
) -> t.Callable[[StudyMetadataDTO], bool]:
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
    user: t.Optional[JWTUser],
    studies: t.Sequence[t.Union[Study, StudyMetadataDTO]],
    permission_type: StudyPermissionType,
    *,
    raising: bool = True,
) -> bool:
    """
    Asserts whether the provided user has the required permissions on the given studies.

    Args:
        user: The user whose permissions need to be verified.
        studies: The studies for which permissions need to be verified.
        permission_type: The type of permission to be checked for the user.
        raising: If set to `True`, raises `UserHasNotPermissionError` when the permission check fails.

    Returns:
        `True` if the user has the required permissions, `False` otherwise.

    Raises:
        `UserHasNotPermissionError`: If the raising parameter is set to `True`
            and the user does not have the required permissions.
    """
    if not user:
        logger.error("FAIL permission: user is not logged")
        raise UserHasNotPermissionError()
    msg = {
        0: f"FAIL permissions: user '{user}' has no access to any study",
        1: f"FAIL permissions: user '{user}' does not have {permission_type.value} permission on {studies[0].id}",
        2: f"FAIL permissions: user '{user}' does not have {permission_type.value} permission on all studies",
    }[min(len(studies), 2)]
    infos = (PermissionInfo.from_study(study) for study in studies)
    if any(not check_permission(user, permission_info, permission_type) for permission_info in infos):
        logger.error(msg)
        if raising:
            raise UserHasNotPermissionError(msg)
        return False
    return True


def assert_permission(
    user: t.Optional[JWTUser],
    study: t.Optional[t.Union[Study, StudyMetadataDTO]],
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

    Returns:
        `True` if the user has the required permissions, `False` otherwise.

    Raises:
        `UserHasNotPermissionError`: If the raising parameter is set to `True`
            and the user does not have the required permissions.
    """
    studies = [study] if study else []
    return assert_permission_on_studies(user, studies, permission_type, raising=raising)


MATRIX_INPUT_DAYS_COUNT = 365

MONTHS = calendar.month_name[1:]

DAY_NAMES = calendar.day_name[:]


def get_start_date(
    file_study: FileStudy,
    output_id: t.Optional[str] = None,
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
    starting_month = t.cast(str, config.get("first-month-in-year"))
    starting_day = t.cast(str, config.get("january.1st"))
    leapyear = t.cast(bool, config.get("leapyear"))
    first_week_day = t.cast(str, config.get("first.weekday"))
    start_offset = t.cast(int, config.get("simulation.start"))
    end = t.cast(int, config.get("simulation.end"))

    starting_month_index = MONTHS.index(starting_month.title()) + 1
    starting_day_index = DAY_NAMES.index(starting_day.title())
    target_year = 2018
    while True:
        if leapyear == calendar.isleap(target_year):
            first_day = datetime(target_year, starting_month_index, 1)
            if first_day.weekday() == starting_day_index:
                break
        target_year += 1

    start_offset_days = timedelta(days=(0 if output_id is None else start_offset - 1))
    start_date = datetime(target_year, starting_month_index, 1) + start_offset_days
    # base case is DAILY
    steps = MATRIX_INPUT_DAYS_COUNT if output_id is None else end - start_offset + 1
    if level == StudyDownloadLevelDTO.HOURLY:
        steps = steps * 24
    elif level == StudyDownloadLevelDTO.ANNUAL:
        steps = 1
    elif level == StudyDownloadLevelDTO.WEEKLY:
        steps = math.ceil(steps / 7)
    elif level == StudyDownloadLevelDTO.MONTHLY:
        end_date = start_date + timedelta(days=steps)
        same_year = end_date.year == start_date.year
        if same_year:
            steps = 1 + end_date.month - start_date.month
        else:
            steps = (13 - start_date.month) + end_date.month

    first_week_day_index = DAY_NAMES.index(first_week_day)
    first_week_offset = 0
    for first_week_offset in range(7):
        first_day = start_date + timedelta(days=first_week_offset)
        if first_day.weekday() == first_week_day_index:
            break
    first_week_size = first_week_offset if first_week_offset != 0 else 7

    return MatrixIndex.construct(
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
    output_list_filter: t.Optional[t.List[str]] = None,
    denormalize: bool = True,
    output_src_path: t.Optional[Path] = None,
) -> None:
    start_time = time.time()

    output_src_path = output_src_path or study_dir / "output"
    output_dest_path = dest / "output"

    def ignore_outputs(directory: str, _: t.Sequence[str]) -> t.Sequence[str]:
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
    study = study_factory.create_from_fs(dest, "", use_cache=False)
    if denormalize:
        study.tree.denormalize()
        duration = "{:.3f}".format(time.time() - stop_time)
        logger.info(f"Study '{study_dir}' denormalized in {duration}s")
