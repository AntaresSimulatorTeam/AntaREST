# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

"""
Unit tests for DatabaseScenarioBuilderDAO.
"""

from antarest.study.business.model.link_model import Link
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.scenario_builder_model import Ruleset, ScenarioType
from antarest.study.business.model.sts_model import STStorage, STStorageAdditionalConstraint
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


def _setup_areas(dao: DatabaseStudyDao, *area_names: str) -> None:
    for name in area_names:
        dao.save_area(name)


def test_save_empty_ruleset(dao: DatabaseStudyDao) -> None:
    dao.save_scenario_builder(Ruleset())
    assert dao.get_ruleset() == Ruleset()


def test_save_ruleset_with_area_scenarios(dao: DatabaseStudyDao) -> None:
    ruleset = Ruleset(
        load={"fr": {"0": 1, "1": 2}},
        wind={"de": {"0": 3}},
    )
    dao.save_scenario_builder(ruleset)
    result = dao.get_ruleset()

    assert result.load == {"fr": {"0": 1, "1": 2}}
    assert result.wind == {"de": {"0": 3}}


def test_save_ruleset_with_all_area_types(dao: DatabaseStudyDao) -> None:
    ruleset = Ruleset(
        load={"fr": {"0": 1}},
        hydro={"fr": {"0": 2}},
        wind={"fr": {"0": 3}},
        solar={"fr": {"0": 4}},
        hydro_initial_levels={"fr": {"0": 0.5}},
        hydro_final_levels={"fr": {"0": 0.8}},
        hydro_generation_power={"fr": {"0": 5}},
    )
    dao.save_scenario_builder(ruleset)
    result = dao.get_ruleset()

    assert result.load == {"fr": {"0": 1}}
    assert result.hydro == {"fr": {"0": 2}}
    assert result.wind == {"fr": {"0": 3}}
    assert result.solar == {"fr": {"0": 4}}
    assert result.hydro_initial_levels == {"fr": {"0": 0.5}}
    assert result.hydro_final_levels == {"fr": {"0": 0.8}}
    assert result.hydro_generation_power == {"fr": {"0": 5}}


def test_save_ruleset_with_link_scenarios(dao: DatabaseStudyDao) -> None:
    _setup_areas(dao, "fr", "de")
    dao.save_link(Link(area1="de", area2="fr"))
    ruleset = Ruleset(ntc={"de / fr": {"0": 1, "1": 2}})
    dao.save_scenario_builder(ruleset)
    result = dao.get_ruleset()

    assert result.ntc == {"de / fr": {"0": 1, "1": 2}}


def test_save_ruleset_with_binding_constraints(dao: DatabaseStudyDao) -> None:
    ruleset = Ruleset(binding_constraints={"group1": {"0": 5, "1": 6}})
    dao.save_scenario_builder(ruleset)
    result = dao.get_ruleset()

    assert result.binding_constraints == {"group1": {"0": 5, "1": 6}}


def test_save_ruleset_with_thermal_scenarios(dao: DatabaseStudyDao) -> None:
    _setup_areas(dao, "fr")
    dao.save_thermal("fr", ThermalCluster(id="gas_cluster", name="Gas Cluster"))
    ruleset = Ruleset(thermal={"fr": {"gas_cluster": {"0": 1, "1": 2}}})
    dao.save_scenario_builder(ruleset)
    result = dao.get_ruleset()

    assert result.thermal == {"fr": {"gas_cluster": {"0": 1, "1": 2}}}


def test_save_ruleset_with_renewable_scenarios(dao: DatabaseStudyDao) -> None:
    _setup_areas(dao, "de")
    dao.save_renewable("de", RenewableCluster(id="wind_farm", name="Wind Farm"))
    ruleset = Ruleset(renewable={"de": {"wind_farm": {"0": 3}}})
    dao.save_scenario_builder(ruleset)
    result = dao.get_ruleset()

    assert result.renewable == {"de": {"wind_farm": {"0": 3}}}


def test_save_ruleset_with_storage_inflows(dao: DatabaseStudyDao) -> None:
    _setup_areas(dao, "fr")
    dao.save_st_storage("fr", STStorage(id="battery_1", name="Battery 1"))
    ruleset = Ruleset(storage_inflows={"fr": {"battery_1": {"0": 4, "1": 5}}})
    dao.save_scenario_builder(ruleset)
    result = dao.get_ruleset()

    assert result.storage_inflows == {"fr": {"battery_1": {"0": 4, "1": 5}}}


def test_save_ruleset_with_storage_constraints(dao: DatabaseStudyDao) -> None:
    _setup_areas(dao, "fr")
    dao.save_st_storage("fr", STStorage(id="battery", name="Battery"))
    dao.save_st_storage_additional_constraints(
        "fr",
        storage_id="battery",
        constraints=[STStorageAdditionalConstraint(id="constraint_a", name="Constraint A")],
    )
    ruleset = Ruleset(storage_constraints={"fr": {"battery": {"constraint_a": {"0": 10, "1": 20}}}})
    dao.save_scenario_builder(ruleset)
    result = dao.get_ruleset()

    assert result.storage_constraints == {"fr": {"battery": {"constraint_a": {"0": 10, "1": 20}}}}


def test_save_replaces_previous_ruleset(dao: DatabaseStudyDao) -> None:
    dao.save_scenario_builder(Ruleset(load={"fr": {"0": 1}}))
    dao.save_scenario_builder(Ruleset(wind={"de": {"0": 2}}))
    result = dao.get_ruleset()

    assert result.load == {}
    assert result.wind == {"de": {"0": 2}}


def test_get_scenario_by_type_area(dao: DatabaseStudyDao) -> None:
    dao.save_scenario_builder(Ruleset(load={"fr": {"0": 1}, "de": {"0": 2}}))

    result = dao.get_scenario_by_type(ScenarioType.LOAD)
    assert result == {"fr": {"0": 1}, "de": {"0": 2}}


def test_get_scenario_by_type_link(dao: DatabaseStudyDao) -> None:
    _setup_areas(dao, "fr", "de")
    dao.save_link(Link(area1="de", area2="fr"))
    dao.save_scenario_builder(Ruleset(ntc={"de / fr": {"0": 7}}))

    result = dao.get_scenario_by_type(ScenarioType.LINK)
    assert result == {"de / fr": {"0": 7}}


def test_get_scenario_by_type_binding_constraints(dao: DatabaseStudyDao) -> None:
    dao.save_scenario_builder(Ruleset(binding_constraints={"group1": {"0": 5}}))

    result = dao.get_scenario_by_type(ScenarioType.BINDING_CONSTRAINTS)
    assert result == {"group1": {"0": 5}}


def test_get_scenario_by_type_thermal(dao: DatabaseStudyDao) -> None:
    _setup_areas(dao, "fr")
    dao.save_thermal("fr", ThermalCluster(id="gas", name="Gas"))
    dao.save_thermal("fr", ThermalCluster(id="nuc", name="Nuc"))
    dao.save_scenario_builder(Ruleset(thermal={"fr": {"gas": {"0": 1}, "nuc": {"0": 2}}}))

    result = dao.get_scenario_by_type(ScenarioType.THERMAL)
    assert result == {"fr": {"gas": {"0": 1}, "nuc": {"0": 2}}}


def test_get_scenario_by_type_storage_inflows(dao: DatabaseStudyDao) -> None:
    _setup_areas(dao, "fr")
    dao.save_st_storage("fr", STStorage(id="battery_1", name="Battery 1"))
    dao.save_scenario_builder(Ruleset(storage_inflows={"fr": {"battery_1": {"0": 4}}}))

    result = dao.get_scenario_by_type(ScenarioType.SHORT_TERM_STORAGE_INFLOWS)
    assert result == {"fr": {"battery_1": {"0": 4}}}


def test_get_scenario_by_type_storage_constraints(dao: DatabaseStudyDao) -> None:
    _setup_areas(dao, "fr")
    dao.save_st_storage("fr", STStorage(id="battery", name="Battery"))
    dao.save_st_storage_additional_constraints(
        "fr",
        storage_id="battery",
        constraints=[STStorageAdditionalConstraint(id="c1", name="C1")],
    )
    dao.save_scenario_builder(Ruleset(storage_constraints={"fr": {"battery": {"c1": {"0": 10}}}}))

    result = dao.get_scenario_by_type(ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS)
    assert result == {"fr": {"battery": {"c1": {"0": 10}}}}


def test_get_scenario_by_type_returns_empty_when_no_data(dao: DatabaseStudyDao) -> None:
    dao.save_scenario_builder(Ruleset())

    result = dao.get_scenario_by_type(ScenarioType.SOLAR)
    assert result == {}


def test_get_scenario_by_type_does_not_mix_scenario_types(dao: DatabaseStudyDao) -> None:
    dao.save_scenario_builder(
        Ruleset(
            load={"fr": {"0": 1}},
            wind={"fr": {"0": 99}},
        )
    )

    assert dao.get_scenario_by_type(ScenarioType.LOAD) == {"fr": {"0": 1}}
    assert dao.get_scenario_by_type(ScenarioType.WIND) == {"fr": {"0": 99}}
