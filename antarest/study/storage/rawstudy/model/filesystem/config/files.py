import json
import logging
import re
import tempfile
import zipfile
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

from antarest.core.model import JSON
from antarest.core.utils.utils import extract_file_to_tmp_dir
from antarest.study.storage.rawstudy.io.reader import (
    IniReader,
    MultipleSameKeysIniReader,
)
from antarest.study.storage.rawstudy.model.filesystem.config.exceptions import (
    SimulationParsingError,
    XpansionParsingError,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    BindingConstraintDTO,
    Cluster,
    DistrictSet,
    FileStudyTreeConfig,
    Link,
    Simulation,
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import (
    DUPLICATE_KEYS,
)

logger = logging.getLogger(__name__)


class FileType(Enum):
    TXT = "txt"
    SIMPLE_INI = "simple_ini"
    MULTI_INI = "multi_ini"


class FileTypeNotSupportedException(Exception):
    pass


def build(
    study_path: Path, study_id: str, output_path: Optional[Path] = None
) -> "FileStudyTreeConfig":
    """
    Extract data from filesystem to build config study.
    Args:
        study_path: study_path with files inside.
        study_id: uuid of the study
        output_path: output_path if not in study_path/output

    Returns: study config fill with data

    """
    (sns, asi, enr_modelling) = _parse_parameters(study_path)

    study_path_without_zip_extension = study_path.parent / (
        study_path.stem if study_path.suffix == ".zip" else study_path.name
    )

    return FileStudyTreeConfig(
        study_path=study_path,
        output_path=output_path or study_path / "output",
        path=study_path_without_zip_extension,
        study_id=study_id,
        version=_parse_version(study_path),
        areas=_parse_areas(study_path),
        sets=_parse_sets(study_path),
        outputs=_parse_outputs(output_path or study_path / "output"),
        bindings=_parse_bindings(study_path),
        store_new_set=sns,
        archive_input_series=asi,
        enr_modelling=enr_modelling,
        zip_path=study_path if study_path.suffix == ".zip" else None,
    )


def _extract_data_from_file(
    root: Path,
    inside_root_path: Path,
    file_type: FileType,
    multi_ini_keys: Optional[List[str]] = None,
) -> Any:
    tmp_dir = None
    try:
        if root.suffix == ".zip":
            output_data_path, tmp_dir = extract_file_to_tmp_dir(
                root, inside_root_path
            )
        else:
            output_data_path = root / inside_root_path

        if file_type == FileType.TXT:
            output_data: Any = output_data_path.read_text().split("\n")
        elif file_type == FileType.MULTI_INI:
            output_data = MultipleSameKeysIniReader(multi_ini_keys).read(
                output_data_path
            )
        elif file_type == FileType.SIMPLE_INI:
            output_data = IniReader().read(output_data_path)
        else:
            raise FileTypeNotSupportedException()
    finally:
        if tmp_dir:
            tmp_dir.cleanup()

    return output_data


def _parse_version(path: Path) -> int:
    study_info = _extract_data_from_file(
        root=path,
        inside_root_path=Path("study.antares"),
        file_type=FileType.SIMPLE_INI,
    )
    version: int = study_info.get("antares", {}).get("version", -1)
    return version


def _parse_parameters(path: Path) -> Tuple[bool, List[str], str]:
    general = _extract_data_from_file(
        root=path,
        inside_root_path=Path("settings/generaldata.ini"),
        file_type=FileType.MULTI_INI,
    )

    store_new_set: bool = general.get("output", {}).get("storenewset", False)
    archive_input_series: List[str] = [
        e.strip()
        for e in general.get("output", {})
        .get("archives", "")
        .strip()
        .split(",")
        if e.strip()
    ]
    enr_modelling: str = general.get("other preferences", {}).get(
        "renewable-generation-modelling", "aggregated"
    )
    return store_new_set, archive_input_series, enr_modelling


def _parse_bindings(root: Path) -> List[BindingConstraintDTO]:
    bindings = _extract_data_from_file(
        root=root,
        inside_root_path=Path(
            "input/bindingconstraints/bindingconstraints.ini"
        ),
        file_type=FileType.SIMPLE_INI,
    )
    output_list = []
    for bind in bindings.values():
        area_set = set()
        # contains a set of strings in the following format: "area.cluster"
        cluster_set = set()
        for key in bind:
            if "%" in key:
                areas = key.split("%", 1)
                area_set.add(areas[0])
                area_set.add(areas[1])
            elif "." in key:
                cluster_set.add(key)
                area_set.add(key.split(".", 1)[0])

        output_list.append(
            BindingConstraintDTO(
                id=bind["id"], areas=area_set, clusters=cluster_set
            )
        )

    return output_list


def _parse_sets(root: Path) -> Dict[str, DistrictSet]:
    obj = _extract_data_from_file(
        root=root,
        inside_root_path=Path("input/areas/sets.ini"),
        file_type=FileType.MULTI_INI,
        multi_ini_keys=["+", "-"],
    )
    return {
        transform_name_to_id(name): DistrictSet(
            areas=item.get(
                "-"
                if item.get("apply-filter", "remove-all") == "add-all"
                else "+"
            ),
            name=item.get("caption"),
            inverted_set=item.get("apply-filter", "remove-all") == "add-all",
            output=item.get("output", True),
        )
        for name, item in obj.items()
    }


def _parse_areas(root: Path) -> Dict[str, Area]:
    areas = _extract_data_from_file(
        root=root,
        inside_root_path=Path("input/areas/list.txt"),
        file_type=FileType.TXT,
    )
    areas = [a for a in areas if a != ""]
    return {transform_name_to_id(a): parse_area(root, a) for a in areas}


def _parse_outputs(output_path: Path) -> Dict[str, Simulation]:
    if not output_path.is_dir():
        return {}
    sims = {}
    # Paths are sorted to have the folders _before_ the ZIP files with the same name.
    for path in sorted(output_path.iterdir()):
        suffix = path.suffix.lower()
        path_name = path.name
        try:
            if suffix == ".tmp" or path_name.startswith("~"):
                continue
            elif suffix == ".zip":
                if path.stem not in sims:
                    if simulation := parse_simulation_zip(path):
                        sims[path.stem] = simulation
            elif (path / "about-the-study/parameters.ini").exists():
                if simulation := parse_simulation(
                    path, canonical_name=path_name
                ):
                    sims[path_name] = simulation
        except SimulationParsingError as exc:
            logger.warning(str(exc), exc_info=True)
    return sims


def parse_simulation_zip(path: Path) -> Simulation:
    with tempfile.TemporaryDirectory(
        dir=path.parent, prefix=f"~{path.stem}-", suffix=".tmp"
    ) as output_dir:
        try:
            with zipfile.ZipFile(path) as zf:
                zf.extractall(output_dir)
        except zipfile.BadZipFile as exc:
            raise SimulationParsingError(path, f"Bad ZIP file: {exc}") from exc
        simulation = parse_simulation(
            Path(output_dir), canonical_name=path.stem
        )
        simulation.archived = True
        return simulation


def _parse_xpansion_version(path: Path) -> str:
    xpansion_json = path / "expansion" / "out.json"
    try:
        content = xpansion_json.read_text(encoding="utf-8")
        obj = json.loads(content)
        return str(obj["antares_xpansion"]["version"])
    except FileNotFoundError:
        return ""
    except json.JSONDecodeError as exc:
        raise XpansionParsingError(
            xpansion_json, f"invalid JSON format: {exc}"
        ) from exc
    except KeyError as exc:
        raise XpansionParsingError(
            xpansion_json, f"key '{exc}' not found in JSON object"
        ) from exc


_regex_eco_adq = re.compile("^([0-9]{8}-[0-9]{4})(eco|adq)-?(.*)")
match_eco_adq = _regex_eco_adq.match


def parse_simulation(path: Path, canonical_name: str) -> Simulation:
    modes = {"eco": "economy", "adq": "adequacy"}
    match = match_eco_adq(canonical_name)
    if match is None:
        raise SimulationParsingError(
            path,
            reason=f"Filename '{canonical_name}' doesn't match {_regex_eco_adq.pattern}",
        )

    try:
        xpansion = _parse_xpansion_version(path)
    except XpansionParsingError as exc:
        # There is something wrong with Xpansion, let's assume it is not used!
        logger.warning(str(exc), exc_info=True)
        xpansion = ""

    ini_path = path / "about-the-study" / "parameters.ini"
    reader = MultipleSameKeysIniReader(DUPLICATE_KEYS)
    try:
        obj: JSON = reader.read(ini_path)
    except FileNotFoundError:
        raise SimulationParsingError(
            path,
            f"Parameters file '{ini_path.relative_to(path)}' not found",
        ) from None

    error = not (path / "checkIntegrity.txt").exists()
    return Simulation(
        date=match.group(1),
        mode=modes[match.group(2)],
        name=match.group(3),
        nbyears=obj["general"]["nbyears"],
        by_year=obj["general"]["year-by-year"],
        synthesis=obj["output"]["synthesis"],
        error=error,
        playlist=list(get_playlist(obj) or {}),
        archived=False,
        xpansion=xpansion,
    )


def get_playlist(config: JSON) -> Optional[Dict[int, float]]:
    general_config = config.get("general", {})
    nb_years = cast(int, general_config.get("nbyears"))
    playlist_activated = cast(bool, general_config.get("user-playlist", False))
    if not playlist_activated:
        return None
    playlist_config = config.get("playlist", {})
    playlist_reset = playlist_config.get("playlist_reset", True)
    added = playlist_config.get("playlist_year +", [])
    removed = playlist_config.get("playlist_year -", [])
    weights = {}
    for year_weight in playlist_config.get("playlist_year_weight", []):
        year_weight_elements = year_weight.split(",")
        weights[int(year_weight_elements[0])] = float(year_weight_elements[1])
    if playlist_reset:
        return {
            year + 1: weights.get(year, 1)
            for year in range(nb_years)
            if year not in removed
        }
    return {
        year + 1: weights.get(year, 1) for year in added if year not in removed
    }


def parse_area(root: Path, area: str) -> "Area":
    area_id = transform_name_to_id(area)
    return Area(
        name=area,
        links=_parse_links(root, area_id),
        thermals=_parse_thermal(root, area_id),
        renewables=_parse_renewables(root, area_id),
        filters_synthesis=_parse_filters_synthesis(root, area_id),
        filters_year=_parse_filters_year(root, area_id),
    )


def _parse_thermal(root: Path, area: str) -> List[Cluster]:
    list_ini = _extract_data_from_file(
        root=root,
        inside_root_path=Path(f"input/thermal/clusters/{area}/list.ini"),
        file_type=FileType.SIMPLE_INI,
    )
    return [
        Cluster(
            id=transform_name_to_id(key),
            enabled=list_ini.get(key, {}).get("enabled", True),
            name=list_ini.get(key, {}).get("name", key),
        )
        for key in list(list_ini.keys())
    ]


def _parse_renewables(root: Path, area: str) -> List[Cluster]:
    try:
        list_ini = _extract_data_from_file(
            root=root,
            inside_root_path=Path(
                f"input/renewables/clusters/{area}/list.ini"
            ),
            file_type=FileType.SIMPLE_INI,
        )
        return [
            Cluster(
                id=transform_name_to_id(key),
                enabled=list_ini.get(key, {}).get("enabled", True),
                name=list_ini.get(key, {}).get("name", None),
            )
            for key in list(list_ini.keys())
        ]
    except Exception:
        return []


def _parse_links(root: Path, area: str) -> Dict[str, Link]:
    properties_ini = _extract_data_from_file(
        root=root,
        inside_root_path=Path(f"input/links/{area}/properties.ini"),
        file_type=FileType.SIMPLE_INI,
    )
    return {
        link: Link.from_json(properties_ini[link])
        for link in list(properties_ini.keys())
    }


def _parse_filters_synthesis(root: Path, area: str) -> List[str]:
    optimization = _extract_data_from_file(
        root=root,
        inside_root_path=Path(f"input/areas/{area}/optimization.ini"),
        file_type=FileType.SIMPLE_INI,
    )
    filters: str = optimization["filtering"]["filter-synthesis"]
    return Link.split(filters)


def _parse_filters_year(root: Path, area: str) -> List[str]:
    optimization = _extract_data_from_file(
        root=root,
        inside_root_path=Path(f"input/areas/{area}/optimization.ini"),
        file_type=FileType.SIMPLE_INI,
    )
    filters: str = optimization["filtering"]["filter-year-by-year"]
    return Link.split(filters)
