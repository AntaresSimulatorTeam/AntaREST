import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, cast

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.io.reader import (
    IniReader,
    MultipleSameKeysIniReader,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    Area,
    Simulation,
    Link,
    DistrictSet,
    transform_name_to_id,
    Cluster,
    BindingConstraintDTO,
)
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import (
    DUPLICATE_KEYS,
)

logger = logging.getLogger(__name__)


class ConfigPathBuilder:
    """
    Fetch information need by StudyConfig from filesystem data
    """

    @staticmethod
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
        (sns, asi, enr_modelling) = ConfigPathBuilder._parse_parameters(
            study_path
        )

        return FileStudyTreeConfig(
            study_path=study_path,
            output_path=output_path or study_path / "output",
            path=study_path,
            study_id=study_id,
            version=ConfigPathBuilder._parse_version(study_path),
            areas=ConfigPathBuilder._parse_areas(study_path),
            sets=ConfigPathBuilder._parse_sets(study_path),
            outputs=ConfigPathBuilder._parse_outputs(
                output_path or study_path / "output"
            ),
            bindings=ConfigPathBuilder._parse_bindings(study_path),
            store_new_set=sns,
            archive_input_series=asi,
            enr_modelling=enr_modelling,
        )

    @staticmethod
    def _parse_version(path: Path) -> int:
        studyinfo = IniReader().read(path / "study.antares")
        version: int = studyinfo.get("antares", {}).get("version", -1)
        return version

    @staticmethod
    def _parse_parameters(path: Path) -> Tuple[bool, List[str], str]:
        general = MultipleSameKeysIniReader().read(
            path / "settings/generaldata.ini"
        )
        store_new_set: bool = general.get("output", {}).get(
            "storenewset", False
        )
        archive_input_series: List[str] = [
            e.strip()
            for e in general.get("output", {})
            .get("archives", "")
            .strip()
            .split(",")
            if e.strip()
        ]
        enr_modelling: str = general.get("other preferences", {}).get(
            "renewables-generation-modelling", "aggregated"
        )
        return store_new_set, archive_input_series, enr_modelling

    @staticmethod
    def _parse_bindings(root: Path) -> List[BindingConstraintDTO]:
        bindings = IniReader().read(
            root / "input/bindingconstraints/bindingconstraints.ini"
        )
        output_list = []
        for id, bind in bindings.items():
            area_set = set()
            cluster_set = (
                set()
            )  # contains a list of strings in the following format: "area.cluster"
            for key in bind.keys():
                if "%" in key:
                    areas = key.split("%")
                    area_set.add(areas[0])
                    area_set.add(areas[1])
                elif "." in key:
                    cluster_set.add(key)
                    area_set.add(key.split(".")[0])

            output_list.append(
                BindingConstraintDTO(
                    id=bind["id"], areas=area_set, clusters=cluster_set
                )
            )

        return output_list

    @staticmethod
    def _parse_sets(root: Path) -> Dict[str, DistrictSet]:
        json = MultipleSameKeysIniReader(["+", "-"]).read(
            root / "input/areas/sets.ini"
        )
        return {
            name.lower(): DistrictSet(
                areas=item.get(
                    "-"
                    if item.get("apply-filter", "remove-all") == "add-all"
                    else "+"
                ),
                name=item.get("caption"),
                inverted_set=item.get("apply-filter", "remove-all")
                == "add-all",
                output=item.get("output", True),
            )
            for name, item in json.items()
        }

    @staticmethod
    def _parse_areas(root: Path) -> Dict[str, Area]:
        areas = (root / "input/areas/list.txt").read_text().split("\n")
        areas = [a for a in areas if a != ""]
        return {
            transform_name_to_id(a): ConfigPathBuilder.parse_area(root, a)
            for a in areas
        }

    @staticmethod
    def _parse_outputs(output_path: Path) -> Dict[str, Simulation]:
        if not output_path.exists():
            return {}

        files = sorted(output_path.iterdir())
        sims = {
            f.name: ConfigPathBuilder.parse_simulation(f)
            for i, f in enumerate(files)
            if (f / "about-the-study").exists()
        }
        return {k: v for k, v in sims.items() if v}

    @staticmethod
    def parse_simulation(path: Path) -> Optional["Simulation"]:
        modes = {"eco": "economy", "adq": "adequacy"}
        regex: Any = re.search(
            "^([0-9]{8}-[0-9]{4})(eco|adq)-?(.*)", path.name
        )
        try:
            (
                nbyears,
                by_year,
                synthesis,
                playlist,
            ) = ConfigPathBuilder._parse_outputs_parameters(path)
            return Simulation(
                date=regex.group(1),
                mode=modes[regex.group(2)],
                name=regex.group(3),
                nbyears=nbyears,
                by_year=by_year,
                synthesis=synthesis,
                error=not (path / "checkIntegrity.txt").exists(),
                playlist=playlist,
            )
        except Exception as e:
            logger.warning(
                f"Failed to parse simulation found at {path}", exc_info=e
            )
        return None

    @staticmethod
    def get_playlist(config: JSON) -> Optional[List[int]]:
        general_config = config.get("general", {})
        nb_years = cast(int, general_config.get("nbyears"))
        playlist_activated = cast(
            bool, general_config.get("user-playlist", False)
        )
        if not playlist_activated:
            return None
        playlist_config = config.get("playlist", {})
        playlist_reset = playlist_config.get("playlist_reset", True)
        added = playlist_config.get("playlist_year +", [])
        removed = playlist_config.get("playlist_year -", [])
        if playlist_reset:
            return [
                year + 1 for year in range(0, nb_years) if year not in removed
            ]
        return [year + 1 for year in added if year not in removed]

    @staticmethod
    def _parse_outputs_parameters(
        path: Path,
    ) -> Tuple[int, bool, bool, Optional[List[int]]]:
        par: JSON = MultipleSameKeysIniReader(DUPLICATE_KEYS).read(
            path / "about-the-study/parameters.ini"
        )
        return (
            par["general"]["nbyears"],
            par["general"]["year-by-year"],
            par["output"]["synthesis"],
            ConfigPathBuilder.get_playlist(par),
        )

    @staticmethod
    def parse_area(root: Path, area: str) -> "Area":
        area_id = transform_name_to_id(area)
        return Area(
            name=area,
            links=ConfigPathBuilder._parse_links(root, area_id),
            thermals=ConfigPathBuilder._parse_thermal(root, area_id),
            renewables=ConfigPathBuilder._parse_renewables(root, area_id),
            filters_synthesis=ConfigPathBuilder._parse_filters_synthesis(
                root, area_id
            ),
            filters_year=ConfigPathBuilder._parse_filters_year(root, area_id),
        )

    @staticmethod
    def _parse_thermal(root: Path, area: str) -> List[Cluster]:
        list_ini = IniReader().read(
            root / f"input/thermal/clusters/{area}/list.ini"
        )
        return [
            Cluster(
                id=transform_name_to_id(key),
                enabled=list_ini.get(key, {}).get("enabled", True),
                name=list_ini.get(key, {}).get("name", key),
            )
            for key in list(list_ini.keys())
        ]

    @staticmethod
    def _parse_renewables(root: Path, area: str) -> List[Cluster]:
        ini_path = root / f"input/renewables/clusters/{area}/list.ini"
        if not ini_path.exists():
            return []

        list_ini = IniReader().read(ini_path)
        return [
            Cluster(
                id=transform_name_to_id(key),
                enabled=list_ini.get(key, {}).get("enabled", True),
                name=list_ini.get(key, {}).get("name", None),
            )
            for key in list(list_ini.keys())
        ]

    @staticmethod
    def _parse_links(root: Path, area: str) -> Dict[str, Link]:
        properties_ini = IniReader().read(
            root / f"input/links/{area}/properties.ini"
        )
        return {
            link: Link.from_json(properties_ini[link])
            for link in list(properties_ini.keys())
        }

    @staticmethod
    def _parse_filters_synthesis(root: Path, area: str) -> List[str]:
        filters: str = IniReader().read(
            root / f"input/areas/{area}/optimization.ini"
        )["filtering"]["filter-synthesis"]
        return Link.split(filters)

    @staticmethod
    def _parse_filters_year(root: Path, area: str) -> List[str]:
        filters: str = IniReader().read(
            root / f"input/areas/{area}/optimization.ini"
        )["filtering"]["filter-year-by-year"]
        return Link.split(filters)
