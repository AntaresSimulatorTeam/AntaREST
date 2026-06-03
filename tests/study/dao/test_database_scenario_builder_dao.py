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
Unit tests for ScenarioBuilderDao — run on both database and filesystem backends.
"""

import pytest

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.scenario_builder_model import RANDOM, Ruleset, ScenarioType
from antarest.study.business.model.sts_model import STStorage, STStorageAdditionalConstraint, initialize_st_storage
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.api.study_dao import StudyDao
from tests.study.dao.utils import save_area


def _setup_areas(dao: StudyDao, *area_names: str) -> None:
    for name in area_names:
        save_area(dao, name)


def _make_storage(dao: StudyDao, **kwargs) -> STStorage:
    """Build a fully-initialized STStorage so DAO write-side validation passes."""
    storage = STStorage(**kwargs)
    initialize_st_storage(storage, dao.get_version())
    return storage


def _set_nb_years(dao: StudyDao, nb_years: int) -> None:
    cfg = dao.get_general_config()
    cfg.nb_years = nb_years
    dao.save_general_config(cfg)


def test_save_empty_ruleset(dao: StudyDao) -> None:
    dao.save_scenario_builder(Ruleset())
    assert dao.get_ruleset() == Ruleset()


def test_save_ruleset_with_area_scenarios(dao: StudyDao) -> None:
    _setup_areas(dao, "fr", "de")
    ruleset = Ruleset(
        load={"fr": {"0": 1, "1": 2}},
        wind={"de": {"0": 3}},
    )
    dao.save_scenario_builder(ruleset)
    result = dao.get_ruleset()

    assert result.load == {"fr": {"0": 1, "1": 2}}
    assert result.wind == {"de": {"0": 3}}


def test_save_ruleset_with_all_area_types(
    dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService],
) -> None:
    # hydro_final_levels + hydro_generation_power require v9.2+
    dao, _ = dao_and_matrix_service
    _setup_areas(dao, "fr")
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


def test_save_ruleset_with_link_scenarios(dao: StudyDao) -> None:
    _setup_areas(dao, "fr", "de")
    dao.save_links([Link(area1="de", area2="fr")])
    ruleset = Ruleset(ntc={"de / fr": {"0": 1, "1": 2}})
    dao.save_scenario_builder(ruleset)
    result = dao.get_ruleset()

    assert result.ntc == {"de / fr": {"0": 1, "1": 2}}


def test_save_ruleset_with_binding_constraints(dao: StudyDao) -> None:
    ruleset = Ruleset(binding_constraints={"group1": {"0": 5, "1": 6}})
    dao.save_scenario_builder(ruleset)
    result = dao.get_ruleset()

    assert result.binding_constraints == {"group1": {"0": 5, "1": 6}}


def test_save_ruleset_with_thermal_scenarios(dao: StudyDao) -> None:
    _setup_areas(dao, "fr")
    dao.save_thermals({"fr": [ThermalCluster(name="Gas_Cluster")]})
    ruleset = Ruleset(thermal={"fr": {"gas_cluster": {"0": 1, "1": 2}}})
    dao.save_scenario_builder(ruleset)
    result = dao.get_ruleset()

    assert result.thermal == {"fr": {"gas_cluster": {"0": 1, "1": 2}}}


def test_save_ruleset_with_renewable_scenarios(dao: StudyDao) -> None:
    _setup_areas(dao, "de")
    dao.save_renewable("de", RenewableCluster(id="wind_farm", name="Wind Farm"))
    ruleset = Ruleset(renewable={"de": {"wind_farm": {"0": 3}}})
    dao.save_scenario_builder(ruleset)
    result = dao.get_ruleset()

    assert result.renewable == {"de": {"wind_farm": {"0": 3}}}


def test_save_ruleset_with_storage_inflows(dao_and_matrix_service) -> None:
    # storage_inflows requires v9.3+
    dao, _ = dao_and_matrix_service
    _setup_areas(dao, "fr")
    dao.save_st_storages({"fr": [_make_storage(dao, id="battery_1", name="Battery 1")]})
    ruleset = Ruleset(storage_inflows={"fr": {"battery_1": {"0": 4, "1": 5}}})
    dao.save_scenario_builder(ruleset)
    result = dao.get_ruleset()

    assert result.storage_inflows == {"fr": {"battery_1": {"0": 4, "1": 5}}}


def test_save_ruleset_with_storage_constraints(dao_and_matrix_service) -> None:
    # storage_constraints requires v9.3+
    dao, _ = dao_and_matrix_service
    _setup_areas(dao, "fr")
    dao.save_st_storages({"fr": [_make_storage(dao, id="battery", name="Battery")]})
    dao.save_st_storage_additional_constraints(
        {"fr": {"battery": [STStorageAdditionalConstraint(name="Constraint_A")]}}
    )
    ruleset = Ruleset(storage_constraints={"fr": {"battery": {"constraint_a": {"0": 10, "1": 20}}}})
    dao.save_scenario_builder(ruleset)
    result = dao.get_ruleset()

    assert result.storage_constraints == {"fr": {"battery": {"constraint_a": {"0": 10, "1": 20}}}}


def test_save_replaces_previous_ruleset(dao: StudyDao) -> None:
    _setup_areas(dao, "fr", "de")
    dao.save_scenario_builder(Ruleset(load={"fr": {"0": 1}}))
    dao.save_scenario_builder(Ruleset(wind={"de": {"0": 2}}))
    result = dao.get_ruleset()

    assert result.load == {}
    assert result.wind == {"de": {"0": 2}}


def test_get_scenario_by_type_area(dao: StudyDao) -> None:
    _setup_areas(dao, "fr", "de")
    dao.save_scenario_builder(Ruleset(load={"fr": {"0": 1}, "de": {"0": 2}}))

    result = dao.get_scenario_by_type(ScenarioType.LOAD)
    assert result == {"fr": {"0": 1}, "de": {"0": 2}}


def test_get_scenario_by_type_binding_constraints(dao: StudyDao) -> None:
    dao.save_scenario_builder(Ruleset(binding_constraints={"group1": {"0": 5}}))

    result = dao.get_scenario_by_type(ScenarioType.BINDING_CONSTRAINTS)
    assert result == {"group1": {"0": 5}}


def test_get_scenario_by_type_thermal(dao: StudyDao) -> None:
    _setup_areas(dao, "fr")
    dao.save_thermals({"fr": [ThermalCluster(name="Gas"), ThermalCluster(name="Nuc")]})
    dao.save_scenario_builder(Ruleset(thermal={"fr": {"gas": {"0": 1}, "nuc": {"0": 2}}}))

    result = dao.get_scenario_by_type(ScenarioType.THERMAL)
    assert result == {"fr": {"gas": {"0": 1}, "nuc": {"0": 2}}}


def test_get_scenario_by_type_storage_constraints(
    dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService],
) -> None:
    # storage_constraints requires v9.3+
    dao, _ = dao_and_matrix_service
    _setup_areas(dao, "fr")
    dao.save_st_storages({"fr": [_make_storage(dao, id="battery", name="Battery")]})
    dao.save_st_storage_additional_constraints({"fr": {"battery": [STStorageAdditionalConstraint(id="c1", name="C1")]}})
    dao.save_scenario_builder(Ruleset(storage_constraints={"fr": {"battery": {"c1": {"0": 10}}}}))

    result = dao.get_scenario_by_type(ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS)
    assert result == {"fr": {"battery": {"c1": {"0": 10}}}}


def test_get_scenario_by_type_returns_empty_when_no_data(dao: StudyDao) -> None:
    dao.save_scenario_builder(Ruleset())

    result = dao.get_scenario_by_type(ScenarioType.SOLAR)
    assert result == {}


def test_get_scenario_by_type_does_not_mix_scenario_types(dao: StudyDao) -> None:
    _setup_areas(dao, "fr")
    dao.save_scenario_builder(
        Ruleset(
            load={"fr": {"0": 1}},
            wind={"fr": {"0": 99}},
        )
    )

    assert dao.get_scenario_by_type(ScenarioType.LOAD) == {"fr": {"0": 1}}
    assert dao.get_scenario_by_type(ScenarioType.WIND) == {"fr": {"0": 99}}


def test_get_scenario_by_type_pads_unsaved_years(dao: StudyDao) -> None:
    """nb_years=3 + value saved only for year 0 → response must pad years 1 and 2 with RANDOM."""
    _setup_areas(dao, "fr")
    _set_nb_years(dao, 3)
    dao.save_scenario_builder(Ruleset(load={"fr": {"0": 1}}))

    assert dao.get_scenario_by_type(ScenarioType.LOAD) == {"fr": {"0": 1, "1": RANDOM, "2": RANDOM}}


def test_get_scenario_by_type_includes_unsaved_areas(dao: StudyDao) -> None:
    """Areas declared but with no saved value must appear in the result, filled with RANDOM."""
    _setup_areas(dao, "fr", "de")
    dao.save_scenario_builder(Ruleset(load={"fr": {"0": 1}}))

    assert dao.get_scenario_by_type(ScenarioType.LOAD) == {"fr": {"0": 1}, "de": {"0": RANDOM}}


def test_get_scenario_by_type_includes_unsaved_thermal_clusters(dao: StudyDao) -> None:
    """Thermal clusters declared but with no saved value must appear in the result."""
    _setup_areas(dao, "fr")
    dao.save_thermals({"fr": [ThermalCluster(name="Gas"), ThermalCluster(name="Nuc")]})
    dao.save_scenario_builder(Ruleset(thermal={"fr": {"gas": {"0": 1}}}))

    assert dao.get_scenario_by_type(ScenarioType.THERMAL) == {"fr": {"gas": {"0": 1}, "nuc": {"0": RANDOM}}}


def test_get_scenario_by_type_includes_unsaved_renewable_clusters(dao: StudyDao) -> None:
    """Renewable clusters declared but with no saved value must appear in the result."""
    _setup_areas(dao, "fr")
    dao.save_renewable("fr", RenewableCluster(id="wind_farm", name="Wind Farm"))
    dao.save_renewable("fr", RenewableCluster(id="solar_farm", name="Solar Farm"))
    dao.save_scenario_builder(Ruleset(renewable={"fr": {"wind_farm": {"0": 3}}}))

    assert dao.get_scenario_by_type(ScenarioType.RENEWABLE) == {
        "fr": {"wind_farm": {"0": 3}, "solar_farm": {"0": RANDOM}}
    }


def test_get_scenario_by_type_includes_unsaved_links(dao: StudyDao) -> None:
    """Links declared but with no saved NTC value must appear in the result."""
    _setup_areas(dao, "fr", "de", "be")
    dao.save_links([Link(area1="de", area2="fr"), Link(area1="be", area2="fr")])
    dao.save_scenario_builder(Ruleset(ntc={"de / fr": {"0": 7}}))

    assert dao.get_scenario_by_type(ScenarioType.LINK) == {
        "de / fr": {"0": 7},
        "be / fr": {"0": RANDOM},
    }


def test_get_scenario_by_type_includes_unsaved_binding_constraints(dao: StudyDao) -> None:
    """Binding-constraint groups declared but with no saved value must appear in the result."""
    from antarest.study.business.model.binding_constraint_model import (
        BindingConstraint,
        BindingConstraintFrequency,
    )

    dao.save_constraints(
        [
            BindingConstraint(name="bc1", group="group1", time_step=BindingConstraintFrequency.HOURLY),
            BindingConstraint(name="bc2", group="group2", time_step=BindingConstraintFrequency.HOURLY),
        ]
    )
    dao.save_scenario_builder(Ruleset(binding_constraints={"group1": {"0": 5}}))

    assert dao.get_scenario_by_type(ScenarioType.BINDING_CONSTRAINTS) == {
        "group1": {"0": 5},
        "group2": {"0": RANDOM},
    }


def test_get_scenario_by_type_includes_unsaved_storage_constraints(
    dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService],
) -> None:
    """This test cover all possible gaps for sts additional constraints :
    * populated constraint with missing year
    * unsaved sibling constraint on same storage
    * unsaved sibling storage on same area
    * unsaved sibling area entirely
    """
    dao, _ = dao_and_matrix_service
    _setup_areas(dao, "fr", "de")
    _set_nb_years(dao, 2)
    dao.save_st_storages(
        {
            "fr": [
                _make_storage(dao, id="battery", name="Battery"),
                _make_storage(dao, id="battery2", name="Battery 2"),
            ],
            "de": [_make_storage(dao, id="battery_d", name="Battery DE")],
        }
    )
    dao.save_st_storage_additional_constraints(
        {
            "fr": {
                "battery": [
                    STStorageAdditionalConstraint(id="c1", name="C1"),
                    STStorageAdditionalConstraint(id="c2", name="C2"),
                ],
                "battery2": [STStorageAdditionalConstraint(id="c3", name="C3")],
            },
            "de": {"battery_d": [STStorageAdditionalConstraint(id="c4", name="C4")]},
        }
    )
    dao.save_scenario_builder(Ruleset(storage_constraints={"fr": {"battery": {"c1": {"0": 10}}}}))

    assert dao.get_scenario_by_type(ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS) == {
        "fr": {
            "battery": {
                "c1": {"0": 10, "1": RANDOM},
                "c2": {"0": RANDOM, "1": RANDOM},
            },
            "battery2": {"c3": {"0": RANDOM, "1": RANDOM}},
        },
        "de": {
            "battery_d": {"c4": {"0": RANDOM, "1": RANDOM}},
        },
    }


def test_scenario_builder_thermal_deleted(dao: StudyDao) -> None:
    _setup_areas(dao, "fr")

    dao.save_thermals({"fr": [ThermalCluster(name="Gas")]})
    dao.save_scenario_builder(Ruleset(thermal={"fr": {"gas": {"0": 1}}}))

    result = dao.get_scenario_by_type(ScenarioType.THERMAL)
    assert result == {"fr": {"gas": {"0": 1}}}

    dao.delete_thermal("fr", "gas")

    result = dao.get_scenario_by_type(ScenarioType.THERMAL)
    assert result == {"fr": {}}


def test_scenario_builder_renewable_deleted(dao: StudyDao) -> None:
    _setup_areas(dao, "de")

    dao.save_renewable("de", RenewableCluster(id="wind_farm", name="Wind Farm"))
    dao.save_scenario_builder(Ruleset(renewable={"de": {"wind_farm": {"0": 3}}}))

    result = dao.get_scenario_by_type(ScenarioType.RENEWABLE)
    assert result == {"de": {"wind_farm": {"0": 3}}}

    dao.delete_renewable("de", RenewableCluster(id="wind_farm", name="Wind Farm"))

    result = dao.get_scenario_by_type(ScenarioType.RENEWABLE)
    assert result == {"de": {}}


def test_scenario_builder_link_deleted(dao: StudyDao) -> None:
    _setup_areas(dao, "de", "fr")

    dao.save_links([Link(area1="de", area2="fr")])
    dao.save_scenario_builder(Ruleset(ntc={"de / fr": {"0": 7}}))

    result = dao.get_scenario_by_type(ScenarioType.LINK)
    assert result == {"de / fr": {"0": 7}}

    dao.delete_link(Link(area1="de", area2="fr"))

    result = dao.get_scenario_by_type(ScenarioType.LINK)
    assert result == {}


def test_scenario_builder_st_storage_deleted(
    dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService],
) -> None:
    # storage_inflows requires v9.3+
    dao, _ = dao_and_matrix_service
    _setup_areas(dao, "fr")

    dao.save_st_storages({"fr": [_make_storage(dao, id="battery_1", name="Battery 1")]})
    dao.save_scenario_builder(Ruleset(storage_inflows={"fr": {"battery_1": {"0": 4}}}))

    result = dao.get_scenario_by_type(ScenarioType.SHORT_TERM_STORAGE_INFLOWS)
    assert result == {"fr": {"battery_1": {"0": 4}}}

    dao.delete_st_storage("fr", STStorage(id="battery_1", name="Battery 1"))

    result = dao.get_scenario_by_type(ScenarioType.SHORT_TERM_STORAGE_INFLOWS)
    assert result == {"fr": {}}


def test_scenario_builder_st_storage_constraint_deleted(
    dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService],
) -> None:
    # storage_constraints requires v9.3+
    dao, _ = dao_and_matrix_service
    _setup_areas(dao, "fr")

    dao.save_st_storages({"fr": [_make_storage(dao, id="battery", name="Battery")]})
    dao.save_st_storage_additional_constraints(
        {"fr": {"battery": [STStorageAdditionalConstraint(name="Constraint_A")]}}
    )
    dao.save_scenario_builder(Ruleset(storage_constraints={"fr": {"battery": {"constraint_a": {"0": 10}}}}))

    result = dao.get_scenario_by_type(ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS)
    assert result == {"fr": {"battery": {"constraint_a": {"0": 10}}}}

    dao.delete_st_storage_additional_constraints("fr", "battery", ["constraint_a"])

    result = dao.get_scenario_by_type(ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS)
    assert result == {"fr": {"battery": {}}}


def test_scenario_builder_st_storage_deleted_cascades_to_constraints(
    dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService],
) -> None:
    # storage_inflows + storage_constraints require v9.3+
    dao, _ = dao_and_matrix_service
    _setup_areas(dao, "fr")

    dao.save_st_storages({"fr": [_make_storage(dao, id="battery", name="Battery")]})
    dao.save_st_storage_additional_constraints({"fr": {"battery": [STStorageAdditionalConstraint(name="C1")]}})
    dao.save_scenario_builder(
        Ruleset(
            storage_inflows={"fr": {"battery": {"0": 4}}},
            storage_constraints={"fr": {"battery": {"c1": {"0": 10}}}},
        )
    )

    assert dao.get_scenario_by_type(ScenarioType.SHORT_TERM_STORAGE_INFLOWS) == {"fr": {"battery": {"0": 4}}}
    assert dao.get_scenario_by_type(ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS) == {
        "fr": {"battery": {"c1": {"0": 10}}}
    }

    dao.delete_st_storage("fr", STStorage(id="battery", name="Battery"))

    assert dao.get_scenario_by_type(ScenarioType.SHORT_TERM_STORAGE_INFLOWS) == {"fr": {}}
    assert dao.get_scenario_by_type(ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS) == {"fr": {}}


def test_scenario_builder_area_deleted_cascades(dao: StudyDao) -> None:
    _setup_areas(dao, "fr")

    dao.save_thermals({"fr": [ThermalCluster(name="Gas")]})
    dao.save_renewable("fr", RenewableCluster(id="wind", name="Wind"))
    dao.save_scenario_builder(
        Ruleset(
            thermal={"fr": {"gas": {"0": 1}}},
            renewable={"fr": {"wind": {"0": 2}}},
        )
    )

    assert dao.get_scenario_by_type(ScenarioType.THERMAL) == {"fr": {"gas": {"0": 1}}}
    assert dao.get_scenario_by_type(ScenarioType.RENEWABLE) == {"fr": {"wind": {"0": 2}}}

    dao.delete_area("fr")

    assert dao.get_scenario_by_type(ScenarioType.THERMAL) == {}
    assert dao.get_scenario_by_type(ScenarioType.RENEWABLE) == {}


def test_scenario_builder_area_deleted_cascades_load(dao: StudyDao) -> None:
    _setup_areas(dao, "fr")

    dao.save_scenario_builder(Ruleset(load={"fr": {"0": 1}}))

    assert dao.get_scenario_by_type(ScenarioType.LOAD) == {"fr": {"0": 1}}

    dao.delete_area("fr")

    assert dao.get_scenario_by_type(ScenarioType.LOAD) == {}


def test_get_scenario_by_type_raises_for_version_incompatible_type(
    dao_860_and_matrix_service: tuple[StudyDao, ISimpleMatrixService],
) -> None:
    """v8.6 has no binding-constraint scenarios → query must raise InvalidFieldForVersionError."""
    dao, _ = dao_860_and_matrix_service

    with pytest.raises(InvalidFieldForVersionError):
        dao.get_scenario_by_type(ScenarioType.BINDING_CONSTRAINTS)
