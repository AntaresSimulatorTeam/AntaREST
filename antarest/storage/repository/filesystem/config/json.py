from pathlib import Path
from typing import List, Dict, Tuple

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


class ConfigJsonBuilder:
    """
    Fetch information need by StudyConfig from json data
    """

    @staticmethod
    def build(study_path: Path, json: JSON, study_id: str) -> "StudyConfig":
        """
        Extract data from json structure to build study config
        Args:
            study_path: root study path to integrate in config
            json: json data
            study_id: study id

        Returns: study config fill with data

        """
        (sns,) = ConfigJsonBuilder._parse_parameters(json)
        return StudyConfig(
            study_id=study_id,
            study_path=study_path,
            areas=ConfigJsonBuilder._parse_areas(json),
            sets=ConfigJsonBuilder._parse_sets(json),
            outputs=ConfigJsonBuilder._parse_outputs(json),
            bindings=ConfigJsonBuilder._parse_bindings(json),
            store_new_set=sns,
        )

    @staticmethod
    def _parse_parameters(json: JSON) -> Tuple[bool]:
        general = json.get("settings", {}).get("generaldata", {})
        store_new_set = general.get("output", {}).get("storenewset", False)

        return (store_new_set,)

    @staticmethod
    def _parse_bindings(json: JSON) -> List[str]:
        bindings = json["input"]["bindingconstraints"]["bindingconstraints"]
        return [bind["id"] for bind in bindings.values()]

    @staticmethod
    def _parse_sets(json: JSON) -> Dict[str, Set]:
        sub_json = json["input"]["areas"]["sets"]
        return {
            name: Set(areas=item.get("+"))
            for name, item in sub_json.items()
            if item.get("output", True)
        }

    @staticmethod
    def _parse_areas(json: JSON) -> Dict[str, Area]:
        areas = list(json["input"]["areas"])
        areas = [
            transform_name_to_id(a) for a in areas if a not in ["sets", "list"]
        ]
        return {a: ConfigJsonBuilder._parse_area(json, a) for a in areas}

    @staticmethod
    def _parse_outputs(json: JSON) -> Dict[str, Simulation]:
        if "output" not in json:
            return {}

        outputs = json["output"]
        return {
            s: ConfigJsonBuilder._parse_simulation(outputs[s])
            for s in outputs.keys()
        }

    @staticmethod
    def _parse_simulation(json: JSON) -> "Simulation":
        (
            nbyears,
            by_year,
            synthesis,
        ) = ConfigJsonBuilder._parse_output_parameters(
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
            error="checkIntegrity" not in json,
        )

    @staticmethod
    def _parse_output_parameters(json: JSON) -> Tuple[int, bool, bool]:
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
    def _parse_thermal(json: JSON, area: str) -> List[ThermalCluster]:
        if area not in json["input"]["thermal"]["clusters"]:
            return []

        list_ini = json["input"]["thermal"]["clusters"][area]["list"]
        return [
            ThermalCluster(
                transform_name_to_id(thermal),
                enabled=list_ini.get(thermal).get("enabled", True),
            )
            for thermal in list(list_ini.keys())
        ]

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
