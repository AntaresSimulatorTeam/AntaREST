from typing import Any, Dict, Optional

from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.settings.scenariobuilder import ScenarioUtils
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder


class ScenarioHandlers:
    @staticmethod
    def handle_generic_scenario(config, nb_years, file_study, scenario_type):
        """Generic handler for area-based scenarios. (load, hydro, wind, solar)"""
        scenario_config = {scenario_type: {}}
        areas = file_study.config.area_names()

        for scenario, mc_year in config.items():
            parts = scenario.split(",")

            # Generic scenarios have 3 parts e.g. for load (`l,<area>,<year> = <TS number>`)
            if len(parts) < 3:
                continue

            symbol, area, index = parts

            type = ScenarioUtils.SYMBOLS_BY_TYPE.get(symbol)
            if type != scenario_type or type not in ["load", "hydro", "wind", "solar"]:
                raise ValueError("Invalid scenario type.")

            if int(index) >= nb_years:
                continue  # Skip the out of range configurations.

            # Initialize area data structure
            if area not in scenario_config[type]:
                scenario_config[type][area] = {}

            area_data = scenario_config[type][area]

            # Handle area-level data initialization
            if not area_data:
                # Initialize MC years as empty if config value is missing.
                area_data.update({str(year): "" for year in range(nb_years)})
            # Set the existing config value if any.
            area_data[index] = mc_year

        # Generate empty configurations (rand) for all areas.
        for area in areas:
            if area not in scenario_config[scenario_type]:
                scenario_config[scenario_type][area] = {str(year): "" for year in range(nb_years)}

        return scenario_config

    @staticmethod
    def handle_thermal_scenario(config, nb_years, file_study, scenario_type):
        """Handler for thermal scenarios that initializes configurations and updates them with existing data."""
        scenario_config = {scenario_type: {}}
        areas = file_study.config.area_names()

        for scenario, mc_year in config.items():
            parts = scenario.split(",")

            # Thermal scenarios should have exactly 4 parts: `t,<area>,<year>,<cluster>`
            if len(parts) != 4:
                continue

            symbol, area, index, cluster = parts
            cluster = cluster.lower()  # Ensure uniformity in cluster identification

            type = ScenarioUtils.SYMBOLS_BY_TYPE.get(symbol)
            if type != scenario_type:
                raise ValueError("Invalid scenario type.")

            if int(index) >= nb_years:
                continue  # Skip the out of range configurations.

            # Initialize area and cluster.
            if area not in scenario_config[scenario_type]:
                scenario_config[scenario_type][area] = {}
            if cluster not in scenario_config[scenario_type][area]:
                scenario_config[scenario_type][area][cluster] = {}

            scenario_config[scenario_type][area][cluster][index] = mc_year

        # Generate empty configurations (rand) for all areas and clusters.
        for area in areas:
            thermal_ids = file_study.config.get_thermal_ids(area)
            if area not in scenario_config[scenario_type]:
                scenario_config[scenario_type][area] = {}
            for tid in thermal_ids:
                cluster = tid.lower()
                if cluster not in scenario_config[scenario_type][area]:
                    scenario_config[scenario_type][area][cluster] = {str(year): "" for year in range(nb_years)}

        return scenario_config

    @staticmethod
    def handle_ntc_scenario(config, nb_years, file_study, scenario_type):
        """Handler for NTC (network transmission capacity) scenarios."""
        scenario_config = {scenario_type: {}}
        areas = file_study.config.area_names()

        for scenario, mc_year in config.items():
            parts = scenario.split(",")

            symbol, area1, area2, index = parts
            link = f"{area1} / {area2}"

            type = ScenarioUtils.SYMBOLS_BY_TYPE.get(symbol)
            if type != scenario_type:
                raise ValueError("Invalid scenario type.")

            # Initialize the link if it does not exist yet
            if link not in scenario_config[scenario_type]:
                scenario_config[scenario_type][link] = {}

            # Only process further if the year index is within bounds
            if 0 <= int(index) < nb_years:
                scenario_config[scenario_type][link][index] = mc_year

        # Generate empty configurations (rand) for all links.
        for area1 in areas:
            area_links = file_study.config.get_links(area1)
            for area2 in area_links:
                # Form the link key using the area and each connected area
                link = f"{area1.lower()} / {area2.lower()}"
                if link not in scenario_config[scenario_type]:
                    scenario_config[scenario_type][link] = {str(year): "" for year in range(nb_years)}

        return scenario_config

    @staticmethod
    def handle_renewable_scenario(config, nb_years, file_study, scenario_type):
        """Handler for renewable scenarios that initializes configurations and updates them with existing data."""
        scenario_config = {scenario_type: {}}
        areas = file_study.config.area_names()

        # Populate scenario configuration from the config dictionary
        for scenario, mc_year in config.items():
            parts = scenario.split(",")

            # Renewable scenarios should also have exactly 4 parts: `r,<area>,<year>,<cluster>`
            if len(parts) != 4:
                continue

            symbol, area, index, cluster = parts
            cluster = cluster.lower()  # Ensure uniformity in cluster identification

            type = ScenarioUtils.SYMBOLS_BY_TYPE.get(symbol)
            if type != scenario_type:
                raise ValueError("Invalid scenario type.")

            if int(index) >= nb_years:
                continue  # Skip the out of range configurations.

            # Initialize area and cluster if they don't already exist.
            if area not in scenario_config[scenario_type]:
                scenario_config[scenario_type][area] = {}
            if cluster not in scenario_config[scenario_type][area]:
                scenario_config[scenario_type][area][cluster] = {}

            scenario_config[scenario_type][area][cluster][index] = mc_year

        # Generate empty configurations (rand) for all areas and clusters.
        for area in areas:
            renewable_ids = file_study.config.get_renewable_ids(area)
            if area not in scenario_config[scenario_type]:
                scenario_config[scenario_type][area] = {}
            for rid in renewable_ids:
                cluster = rid.lower()
                if cluster not in scenario_config[scenario_type][area]:
                    scenario_config[scenario_type][area][cluster] = {str(year): "" for year in range(nb_years)}

        return scenario_config

    @staticmethod
    def handle_binding_constraints_scenario(config, nb_years, file_study, scenario_type):
        """Handler for binding constraints (BC) scenarios that initializes configurations based on existing BC groups."""
        scenario_config = {scenario_type: {}}
        bc_groups = file_study.config.get_binding_constraint_groups()

        for scenario, mc_year in config.items():
            parts = scenario.split(",")

            # Expect format: `bc,<group>,<year> = <TS number>`
            if len(parts) != 3:
                continue

            (
                symbol,
                group,
                index,
            ) = parts

            type = ScenarioUtils.SYMBOLS_BY_TYPE.get(symbol)
            if type != scenario_type:
                raise ValueError("Invalid scenario type.")

            # Initialize the group if it does not exist
            if group not in scenario_config[scenario_type]:
                scenario_config[scenario_type][group] = {str(y): "" for y in range(nb_years)}

            # Only set the configuration year if it's within the valid range
            if 0 <= int(index) < nb_years:
                scenario_config[scenario_type][group][index] = mc_year

        # Generate empty configurations (rand) for all BC groups.
        for group in bc_groups:
            if group.lower() not in scenario_config[scenario_type]:
                scenario_config[scenario_type][group.lower()] = {str(year): "" for year in range(nb_years)}

        return scenario_config

    @staticmethod
    def parse_config_by_type(scenario_config, nb_years, file_study, scenario_type):
        """Route to the appropriate handler based on scenario type."""

        handlers = {
            "load": ScenarioHandlers.handle_generic_scenario,
            "thermal": ScenarioHandlers.handle_thermal_scenario,
            "hydro": ScenarioHandlers.handle_generic_scenario,
            "wind": ScenarioHandlers.handle_generic_scenario,
            "solar": ScenarioHandlers.handle_generic_scenario,
            "ntc": ScenarioHandlers.handle_ntc_scenario,
            "renewable": ScenarioHandlers.handle_renewable_scenario,
            "bindingConstraints": ScenarioHandlers.handle_binding_constraints_scenario,
        }

        handler = handlers.get(scenario_type)
        return handler(scenario_config, nb_years, file_study, scenario_type)


class ScenarioBuilderManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def _get_file_study(self, study: Study) -> FileStudy:
        """
        Helper function to get raw study data.
        """
        return self.storage_service.get_storage(study).get_raw(study)

    @staticmethod
    def create_scenario_key(scenario_type: str, area: str, year: str, cluster: Optional[str] = None) -> str:
        """
        Generate configuration keys based on the scenario type and given parameters.
        This method adjusts keys for different scenarios including clusters and NTC links.
        """
        symbol = ScenarioUtils.TYPES_BY_SYMBOL.get(scenario_type)

        if scenario_type in ["thermal", "renewable"]:
            # Keys for scenarios with clusters should include the cluster name
            return f"{symbol},{area},{year},{cluster}"

        if scenario_type == "ntc":
            # Keys for NTC scenarios should split the area into two linked areas
            area1, area2 = map(str.strip, area.split("/"))
            return f"{symbol},{area1},{area2},{year}"

        # Simple area-year key for other types
        return f"{symbol},{area},{year}"

    @staticmethod
    def generate_updates(scenario_config_updates: Dict[str, Dict[str, Dict[str, Dict[str, int]]]]) -> Dict[str, int]:
        updates = {}

        for scenario_type, areas in scenario_config_updates.items():
            for area, configurations in areas.items():
                for key, value in configurations.items():
                    if isinstance(value, dict):
                        for year, val in value.items():
                            cluster = key if scenario_type in ["thermal", "renewable"] else None
                            full_key = ScenarioBuilderManager.create_scenario_key(scenario_type, area, year, cluster)
                            updates[full_key] = val
                    else:
                        full_key = ScenarioBuilderManager.create_scenario_key(scenario_type, area, key)
                        updates[full_key] = value

        return updates

    def get_scenario_by_type(self, study: Study, scenario_type: str) -> Dict[str, Any]:
        if not scenario_type:
            raise ValueError("Scenario type is missing.")

        if scenario_type not in ScenarioUtils.TYPES_BY_SYMBOL:
            raise ValueError(f"Unsupported scenario type: {scenario_type}")

        storage = self.storage_service.get_storage(study)
        file_study = self._get_file_study(study)
        general_settings = storage.get(study, "settings/generaldata/general")
        active_ruleset = general_settings.get("active-rules-scenario", "Default Ruleset")

        nb_years = general_settings.get("nbyears", 0)
        if nb_years <= 0:
            raise ValueError("Number of years must be greater than zero.")

        scenario_config = storage.get(study, f"/settings/scenariobuilder/{active_ruleset}/{scenario_type}")
        if not scenario_config:
            raise ValueError("Scenario configuration is missing or empty.")

        return ScenarioHandlers.parse_config_by_type(
            scenario_config[active_ruleset], nb_years, file_study, scenario_type
        )

    def update_scenario_by_type(
        self, study: Study, scenario_updates: Dict[str, Dict[str, Dict[str, Dict[str, int]]]]
    ) -> None:
        file_study = self._get_file_study(study)
        general_settings = self.storage_service.get_storage(study).get(study, "settings/generaldata/general")
        active_ruleset = general_settings.get("active-rules-scenario", "Default Ruleset")

        updates = ScenarioBuilderManager.generate_updates(scenario_updates)

        update_scenario = UpdateScenarioBuilder(
            data={active_ruleset: updates},
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(study, file_study, [update_scenario], self.storage_service)
