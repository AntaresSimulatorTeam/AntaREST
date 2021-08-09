import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Iterator

from antarest.core.custom_types import JSON
from antarest.study.storage.rawstudy.io.reader import (
    IniReader,
    MultipleSameKeysIniReader,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    Area,
    Simulation,
    Link,
    Set,
    transform_name_to_id,
    Cluster,
)


class ConfigPathBuilder:
    """
    Fetch information need by StudyConfig from filesystem data
    """

    @staticmethod
    def build(study_path: Path, study_id: str) -> "FileStudyTreeConfig":
        """
        Extract data from filesystem to build config study.
        Args:
            study_path: study_path with files inside.
            study_id: uuid of the study

        Returns: study config fill with data

        """
        (sns, asi, enr_modelling) = ConfigPathBuilder._parse_parameters(
            study_path
        )

        return FileStudyTreeConfig(
            study_path=study_path,
            path=study_path,
            study_id=study_id,
            version=ConfigPathBuilder._parse_version(study_path),
            areas=ConfigPathBuilder._parse_areas(study_path),
            sets=ConfigPathBuilder._parse_sets(study_path),
            outputs=ConfigPathBuilder._parse_outputs(study_path),
            bindings=ConfigPathBuilder._parse_bindings(study_path),
            store_new_set=sns,
            archive_input_series=asi,
            enr_modelling=enr_modelling,
        )

    @staticmethod
    def _parse_version(path: Path) -> int:
        studyinfo = IniReader().read(path / "study.antares")
        return studyinfo.get("version", -1)

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
            "renewable-generation-modelling", "aggregated"
        )
        return store_new_set, archive_input_series, enr_modelling

    @staticmethod
    def _parse_bindings(root: Path) -> List[str]:
        bindings = IniReader().read(
            root / "input/bindingconstraints/bindingconstraints.ini"
        )
        return [bind["id"] for bind in bindings.values()]

    @staticmethod
    def _parse_sets(root: Path) -> Dict[str, Set]:
        json = MultipleSameKeysIniReader().read(root / "input/areas/sets.ini")
        return {
            name.lower(): Set(areas=item.get("+"))
            for name, item in json.items()
            if item.get("output", True)
        }

    @staticmethod
    def _parse_areas(root: Path) -> Dict[str, Area]:
        areas = (root / "input/areas/list.txt").read_text().split("\n")
        areas = [transform_name_to_id(a) for a in areas if a != ""]
        return {a: ConfigPathBuilder.parse_area(root, a) for a in areas}

    @staticmethod
    def _parse_outputs(root: Path) -> Dict[str, Simulation]:
        if not (root / "output").exists():
            return {}

        files = sorted((root / "output").iterdir())
        return {
            f.name: ConfigPathBuilder.parse_simulation(f)
            for i, f in enumerate(files)
            if (f / "about-the-study").exists()
        }

    @staticmethod
    def parse_simulation(path: Path) -> "Simulation":
        modes = {"eco": "economy", "adq": "adequacy"}
        regex: Any = re.search(
            "^([0-9]{8}-[0-9]{4})(eco|adq)-?(.*)", path.name
        )
        (
            nbyears,
            by_year,
            synthesis,
        ) = ConfigPathBuilder._parse_outputs_parameters(path)
        return Simulation(
            date=regex.group(1),
            mode=modes[regex.group(2)],
            name=regex.group(3),
            nbyears=nbyears,
            by_year=by_year,
            synthesis=synthesis,
            error=not (path / "checkIntegrity.txt").exists(),
        )

    @staticmethod
    def _parse_outputs_parameters(path: Path) -> Tuple[int, bool, bool]:
        par: JSON = IniReader().read(path / "about-the-study/parameters.ini")
        return (
            par["general"]["nbyears"],
            par["general"]["year-by-year"],
            par["output"]["synthesis"],
        )

    @staticmethod
    def parse_area(root: Path, area: str) -> "Area":
        return Area(
            links=ConfigPathBuilder._parse_links(root, area),
            thermals=ConfigPathBuilder._parse_thermal(root, area),
            renewables=ConfigPathBuilder._parse_renewables(root, area),
            filters_synthesis=ConfigPathBuilder._parse_filters_synthesis(
                root, area
            ),
            filters_year=ConfigPathBuilder._parse_filters_year(root, area),
        )

    @staticmethod
    def _parse_thermal(root: Path, area: str) -> List[Cluster]:
        list_ini = IniReader().read(
            root / f"input/thermal/clusters/{area}/list.ini"
        )
        return [
            Cluster(
                transform_name_to_id(key),
                enabled=list_ini.get(key, {}).get("enabled", True),
                name=transform_name_to_id(key)
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
                transform_name_to_id(key),
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
