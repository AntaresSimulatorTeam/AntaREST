from typing import Any, Dict, Optional

from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder

SCENARIOS = [
    {"type": "load", "symbol": "l"},
    {"type": "thermal", "symbol": "t"},
    {"type": "hydro", "symbol": "h"},
    {"type": "wind", "symbol": "w"},
    {"type": "solar", "symbol": "s"},
    {"type": "ntc", "symbol": "ntc"},
    {"type": "renewable", "symbol": "r"},
    {"type": "bindingConstraints", "symbol": "bc"},
]

types_by_symbol = {scenario['type']: scenario['symbol'] for scenario in SCENARIOS}
symbols_by_type = {scenario["symbol"]: scenario["type"] for scenario in SCENARIOS}


def _generate_clusters_mc_years(nb_years, identifiers, lowercase_ids=False):
    """Helper function to generate a scenario config skeleton based on provided identifiers."""
    if lowercase_ids:
        identifiers = [id.lower() for id in identifiers]
    return {id: {str(year): "" for year in range(nb_years)} for id in identifiers}


def _handle_generic_scenario(config, nb_years, file_study, scenario_type):
    """Generic handler for area-based scenarios. (load, hydro, wind, solar)"""

    scenario_config = {scenario_type: {}}
    areas = file_study.config.area_names()

    for scenario, mc_year in config.items():
        parts = scenario.split(",")

        # Generic scenarios have 3 parts e.g. for load (`l,<area>,<year> = <TS number>`)
        if len(parts) < 3:
            continue

        symbol, area, index = parts

        type = symbols_by_type.get(symbol)
        if type != scenario_type or type not in ['load', 'hydro', 'wind', 'solar']:
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


def _handle_thermal_scenario(config, nb_years, file_study, scenario_type):
    """Handler for thermal scenarios that initializes configurations and updates them with existing data."""
    scenario_config = {"thermal": {}}
    areas = file_study.config.area_names()

    for scenario, mc_year in config.items():
        parts = scenario.split(",")

        # Thermal scenarios should have exactly 4 parts: `t,<area>,<year>,<cluster>`
        if len(parts) != 4:
            continue

        symbol, area, index, cluster = parts
        cluster = cluster.lower()  # Ensure uniformity in cluster identification

        type = symbols_by_type.get(symbol)
        if type != scenario_type:
            raise ValueError("Invalid scenario type.")

        if int(index) >= nb_years:
            continue  # Skip the out of range configurations.

        # Initialize area and cluster.
        if area not in scenario_config["thermal"]:
            scenario_config["thermal"][area] = {}
        if cluster not in scenario_config["thermal"][area]:
            scenario_config["thermal"][area][cluster] = {}

        scenario_config["thermal"][area][cluster][index] = mc_year

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


def _handle_ntc_scenario(config, nb_years, file_study, scenario_type):
    """Handler for NTC (network transmission capacity) scenarios."""
    scenario_config = {scenario_type: {}}
    areas = file_study.config.area_names()

    for scenario, mc_year in config.items():
        parts = scenario.split(",")

        symbol, area1, area2, index = parts
        # Construct the link key using a consistent format
        link = f"{area1} / {area2}"

        type = symbols_by_type.get(symbol)
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


def _handle_renewable_scenario(config, nb_years, file_study, scenario_type):
    """Handler for renewable scenarios that initializes configurations and updates them with existing data."""
    scenario_config = {"renewable": {}}
    areas = file_study.config.area_names()

    # Populate scenario configuration from the config dictionary
    for scenario, mc_year in config.items():
        parts = scenario.split(",")

        # Renewable scenarios should also have exactly 4 parts: `r,<area>,<year>,<cluster>`
        if len(parts) != 4:
            continue

        symbol, area, index, cluster = parts
        cluster = cluster.lower()  # Ensure uniformity in cluster identification

        type = symbols_by_type.get(symbol)
        if type != scenario_type:
            raise ValueError("Invalid scenario type.")

        if int(index) >= nb_years:
            continue  # Skip the out of range configurations.

        # Initialize area and cluster if they don't already exist.
        if area not in scenario_config["renewable"]:
            scenario_config["renewable"][area] = {}
        if cluster not in scenario_config["renewable"][area]:
            scenario_config["renewable"][area][cluster] = {}

        scenario_config["renewable"][area][cluster][index] = mc_year

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


def _handle_binding_constraints_scenario(config, nb_years, file_study, scenario_type):
    """Handler for binding constraints (BC) scenarios that initializes configurations based on existing BC groups."""
    scenario_config = {scenario_type: {}}
    bc_groups = file_study.config.get_binding_constraint_groups()

    for scenario, mc_year in config.items():
        parts = scenario.split(",")

        # Expect format: `bc,<group>,<year> = <TS number>`
        if len(parts) != 3:
            continue

        symbol, group, index, = parts

        type = symbols_by_type.get(symbol)
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


def parse_config_by_handler(scenario_config, nb_years, file_study, scenario_type):
    """Route to the appropriate handler based on scenario type."""
    handlers = {
        'load': _handle_generic_scenario,
        'thermal': _handle_thermal_scenario,
        'hydro': _handle_generic_scenario,
        'wind': _handle_generic_scenario,
        'solar': _handle_generic_scenario,
        'ntc': _handle_ntc_scenario,
        'renewable': _handle_renewable_scenario,
        'bindingConstraints': _handle_binding_constraints_scenario,
    }

    if not scenario_type:
        raise ValueError("Scenario type is missing.")

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

    def get_scenario_by_type(self, study: Study, scenario_type: str = None) -> Dict[str, Any]:
        if scenario_type not in types_by_symbol:
            raise ValueError(f"Unsupported scenario type: {scenario_type}")

        storage = self.storage_service.get_storage(study)
        file_study = self._get_file_study(study)
        general_settings = storage.get(study, "settings/generaldata/general")
        # TODO add default ruleset on empty config studies, if no areas raise an error
        active_ruleset = general_settings.get("active-rules-scenario", "Default Ruleset")
        nb_years = general_settings.get("nbyears", 0)

        if nb_years <= 0:
            raise ValueError("Number of years must be greater than zero.")

        scenario_config = storage.get(study, f"/settings/scenariobuilder/{active_ruleset}/{scenario_type}")

        if not scenario_config:
            raise ValueError("Scenario configuration is missing or empty.")

        return parse_config_by_handler(scenario_config[active_ruleset], nb_years, file_study, scenario_type)

    def update_config(self, study: Study, scenario_updates: Dict[str, Dict[str, Dict[str, Dict[str, int]]]]) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        active_ruleset = self.storage_service.get_storage(study).get(study, "settings/generaldata/general").get(
            "active-rules-scenario", "Default Ruleset")

        def to_valid_key(symbol: str, area: str, index: str, cluster: Optional[str] = None) -> str:
            """
            Generate a valid configuration key based on the provided parameters.
            Handles special formatting for 'ntc' symbols where the area needs to be split.

            Args:
                symbol (str): The symbol indicating the type of scenario (e.g., 't', 'ntc').
                area (str): The area or combined areas, potentially needing splitting for 'ntc'.
                index (str): The index or identifier within the configuration.
                cluster (Optional[str]): The cluster identifier, if applicable.

            Returns:
                str: The correctly formatted key.
            """
            if symbol == "ntc" and " / " in area:
                # Split the area for 'ntc' scenarios, which involve linked areas.
                area1, area2 = area.split(" / ")
                return f"{symbol},{area1},{area2},{index}"
            else:
                # Clusters scenarios key format.
                if cluster:
                    return f"{symbol},{area},{index},{cluster}"
                # Standard key format for non-'ntc' and 'clusters' scenarios.
                return f"{symbol},{area},{index}"

        # Convert the structured scenario data into the flat format expected by the update commands
        def flatten_updates(data: Dict[str, Dict[str, Dict[str, int]]], symbol: str) -> Dict[str, int]:
            flat_data = {}
            for area, clusters_or_indexes in data.items():
                for cluster_or_index, value in clusters_or_indexes.items():
                    if isinstance(value, dict):
                        # If the value is a dictionary, then it's a cluster configuration
                        for index, val in value.items():
                            key = to_valid_key(symbol, area, index, cluster_or_index)
                            flat_data[key] = val
                    else:
                        # If the value is not a dictionary, it's a direct area configuration
                        key = to_valid_key(symbol, area, cluster_or_index)
                        flat_data[key] = value
            return flat_data

        # Process each scenario type in the updates
        updates_to_apply = {}
        for scenario_type, areas in scenario_updates.items():
            symbol = types_by_symbol.get(scenario_type)
            if not symbol:
                continue  # Skip unknown scenario types
            scenario_data = flatten_updates(areas, symbol)
            updates_to_apply.update(scenario_data)

        execute_or_add_commands(
            study,
            file_study,
            [
                UpdateScenarioBuilder(
                    data={active_ruleset: updates_to_apply},
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                )
            ],
            self.storage_service,
        )
