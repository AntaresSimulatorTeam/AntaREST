import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

from antarest.storage.repository.antares_io.reader import (
    IniReader,
    SetsIniReader,
)
from antarest.common.custom_types import JSON
from antarest.storage.repository.filesystem.config.model import (
    StudyConfig,
    Area,
    Simulation,
    Link,
    Set,
    transform_name_to_id,
    ThermalCluster,
)


class ConfigPathBuilder:
    @staticmethod
    def build(study_path: Path) -> "StudyConfig":
        (sns,) = ConfigPathBuilder._parse_parameters(study_path)

        return StudyConfig(
            study_path=study_path,
            areas=ConfigPathBuilder._parse_areas(study_path),
            sets=ConfigPathBuilder._parse_sets(study_path),
            outputs=ConfigPathBuilder._parse_outputs(study_path),
            bindings=ConfigPathBuilder._parse_bindings(study_path),
            store_new_set=sns,
        )

    @staticmethod
    def _parse_parameters(path: Path) -> Tuple[bool]:
        general = IniReader().read(path / "settings/generaldata.ini")
        store_new_set: bool = general.get("output", {}).get(
            "storenewset", False
        )
        return (store_new_set,)

    @staticmethod
    def _parse_bindings(root: Path) -> List[str]:
        bindings = IniReader().read(
            root / "input/bindingconstraints/bindingconstraints.ini"
        )
        return [bind["id"] for bind in bindings.values()]

    @staticmethod
    def _parse_sets(root: Path) -> Dict[str, Set]:
        json = SetsIniReader().read(root / "input/areas/sets.ini")
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
    def _parse_outputs(root: Path) -> Dict[int, Simulation]:
        if not (root / "output").exists():
            return {}

        files = sorted((root / "output").iterdir())
        return {
            i + 1: ConfigPathBuilder.parse_simulation(f)
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
            filters_synthesis=ConfigPathBuilder._parse_filters_synthesis(
                root, area
            ),
            filters_year=ConfigPathBuilder._parse_filters_year(root, area),
        )

    @staticmethod
    def _parse_thermal(root: Path, area: str) -> List[ThermalCluster]:
        list_ini = IniReader().read(
            root / f"input/thermal/clusters/{area}/list.ini"
        )
        return [
            ThermalCluster(
                transform_name_to_id(key),
                enabled=list_ini.get(key, {}).get("enabled", True),
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
