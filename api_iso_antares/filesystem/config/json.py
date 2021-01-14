from pathlib import Path
from typing import List, Dict, Tuple

from api_iso_antares.custom_types import JSON
from api_iso_antares.filesystem.config.model import (
    Config,
    Area,
    Simulation,
    Link,
)


class ConfigJsonBuilder:
    @staticmethod
    def build(study_path: Path, json: JSON) -> "Config":
        return Config(
            study_path=study_path,
            areas=ConfigJsonBuilder._parse_areas(json),
            outputs=ConfigJsonBuilder._parse_outputs(json),
            bindings=ConfigJsonBuilder._parse_bindings(json),
        )

    @staticmethod
    def _parse_bindings(json: JSON) -> List[str]:
        bindings = json["input"]["bindingconstraints"]["bindingconstraints"]
        return [bind["id"] for bind in bindings.values()]

    @staticmethod
    def _parse_areas(json: JSON) -> Dict[str, Area]:
        areas = list(json["input"]["areas"])
        areas = [a for a in areas if a not in ["sets", "list"]]
        return {a: ConfigJsonBuilder._parse_area(json, a) for a in areas}

    @staticmethod
    def _parse_outputs(json: JSON) -> Dict[int, Simulation]:
        if "output" not in json:
            return {}

        outputs = json["output"]
        return {
            int(i): ConfigJsonBuilder._parse_simulation(s)
            for i, s in outputs.items()
        }

    @staticmethod
    def _parse_simulation(json: JSON) -> "Simulation":
        nbyears, by_year, synthesis = ConfigJsonBuilder._parse_parameters(
            json["about-the-study"]["parameters"]
        )
        info = json["info"]["general"]
        return Simulation(
            date=info["date"]
            .replace(".", "")
            .replace(":", "")
            .replace(" ", ""),
            mode=info["mode"].lower(),
            name=info["name"],
            nbyears=nbyears,
            by_year=by_year,
            synthesis=synthesis,
        )

    @staticmethod
    def _parse_parameters(json: JSON) -> Tuple[int, bool, bool]:
        return (
            json["general"]["nbyears"],
            json["general"]["year-by-year"],
            json["output"]["synthesis"],
        )

    @staticmethod
    def _parse_area(json: JSON, area: str) -> "Area":
        return Area(
            links=ConfigJsonBuilder._parse_links(json, area),
            thermals=ConfigJsonBuilder._parse_thermal(json, area),
            filters_synthesis=ConfigJsonBuilder._parse_filters_synthesis(
                json, area
            ),
            filters_year=ConfigJsonBuilder._parse_filters_year(json, area),
        )

    @staticmethod
    def _parse_thermal(json: JSON, area: str) -> List[str]:
        if area not in json["input"]["thermal"]["clusters"]:
            return list()

        list_ini = json["input"]["thermal"]["clusters"][area]["list"]
        return list(list_ini.keys())

    @staticmethod
    def _parse_links(json: JSON, area: str) -> Dict[str, Link]:
        if area not in json["input"]["links"]:
            return dict()

        properties_ini = json["input"]["links"][area]["properties"]
        return {
            link: Link(
                filters_synthesis=Link.split(
                    properties_ini[link]["filter-synthesis"]
                ),
                filters_year=Link.split(
                    properties_ini[link]["filter-year-by-year"]
                ),
            )
            for link in list(properties_ini.keys())
        }

    @staticmethod
    def _parse_filters_synthesis(json: JSON, area: str) -> List[str]:
        filters: str = json["input"]["areas"][area]["optimization"][
            "filtering"
        ]["filter-synthesis"]
        return Link.split(filters)

    @staticmethod
    def _parse_filters_year(json: JSON, area: str) -> List[str]:
        filters: str = json["input"]["areas"][area]["optimization"][
            "filtering"
        ]["filter-year-by-year"]
        return Link.split(filters)
