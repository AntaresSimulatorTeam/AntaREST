import typing as t

import typing_extensions as te

from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder

_HYDRO_LEVEL_PERCENT = 100

_Section: te.TypeAlias = t.MutableMapping[str, t.Union[int, float]]
_Sections: te.TypeAlias = t.MutableMapping[str, _Section]

Ruleset: te.TypeAlias = t.MutableMapping[str, t.Any]
Rulesets: te.TypeAlias = t.MutableMapping[str, Ruleset]


class ScenarioBuilderManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_config(self, study: Study) -> Rulesets:
        sections = t.cast(_Sections, self.storage_service.get_storage(study).get(study, "/settings/scenariobuilder"))

        rulesets: Rulesets = {}
        for ruleset_name, data in sections.items():
            ruleset = rulesets.setdefault(ruleset_name, {})
            for key, value in data.items():
                symbol, *parts = key.split(",")
                scenario = ruleset.setdefault(symbol, {})
                if symbol in ("l", "h", "w", "s", "bc", "hgp"):
                    scenario_area = scenario.setdefault(parts[0], {})
                    scenario_area[parts[1]] = int(value)
                elif symbol in ("hl", "hfl"):
                    scenario_area = scenario.setdefault(parts[0], {})
                    scenario_area[parts[1]] = float(value) * _HYDRO_LEVEL_PERCENT
                elif symbol in ("ntc",):
                    scenario_link = scenario.setdefault(f"{parts[0]} / {parts[1]}", {})
                    scenario_link[parts[2]] = int(value)
                elif symbol in ("t", "r"):
                    scenario_area = scenario.setdefault(parts[0], {})
                    scenario_area_cluster = scenario_area.setdefault(parts[2], {})
                    scenario_area_cluster[parts[1]] = int(value)
                else:  # pragma: no cover
                    raise NotImplementedError(f"Unknown symbol {symbol}")

        return rulesets

    def update_config(self, study: Study, rulesets: Rulesets) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)

        sections: _Sections = {}
        for ruleset_name, ruleset in rulesets.items():
            section = sections[ruleset_name] = {}
            for symbol, data in ruleset.items():
                if symbol in ("l", "h", "w", "s", "bc", "hgp"):
                    _populate_common(section, symbol, data)
                elif symbol in ("hl", "hfl"):
                    _populate_hydro_levels(section, symbol, data)
                elif symbol in ("ntc",):
                    _populate_links(section, symbol, data)
                elif symbol in ("t", "r"):
                    _populate_clusters(section, symbol, data)
                else:  # pragma: no cover
                    raise NotImplementedError(f"Unknown symbol {symbol}")

        context = self.storage_service.variant_study_service.command_factory.command_context
        execute_or_add_commands(
            study,
            file_study,
            [UpdateScenarioBuilder(data=sections, command_context=context)],
            self.storage_service,
        )


def _populate_common(section: _Section, symbol: str, data: t.Mapping[str, t.Mapping[str, t.Any]]) -> None:
    for area, scenario_area in data.items():
        for year, value in scenario_area.items():
            section[f"{symbol},{area},{year}"] = value


def _populate_hydro_levels(section: _Section, symbol: str, data: t.Mapping[str, t.Mapping[str, t.Any]]) -> None:
    for area, scenario_area in data.items():
        for year, value in scenario_area.items():
            if isinstance(value, (int, float)) and value != float("nan"):
                value /= _HYDRO_LEVEL_PERCENT
            section[f"{symbol},{area},{year}"] = value


def _populate_links(section: _Section, symbol: str, data: t.Mapping[str, t.Mapping[str, t.Any]]) -> None:
    for link, scenario_link in data.items():
        for year, value in scenario_link.items():
            area1, area2 = link.split(" / ")
            section[f"{symbol},{area1},{area2},{year}"] = value


def _populate_clusters(section: _Section, symbol: str, data: t.Mapping[str, t.Mapping[str, t.Any]]) -> None:
    for area, scenario_area in data.items():
        for cluster, scenario_area_cluster in scenario_area.items():
            for year, value in scenario_area_cluster.items():
                section[f"{symbol},{area},{year},{cluster}"] = value
