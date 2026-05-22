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

from antarest.study.business.model.area_properties_model import FILTER_OPTIONS, AreaProperties
from antarest.study.business.model.config.advanced_parameters_model import (
    AdvancedParameters,
    RenewableGenerationModeling,
)
from antarest.study.business.model.district_model import District, DistrictApplyFilter
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.sts_model import STStorage, initialize_st_storage
from antarest.study.business.model.thermal_cluster_model import ThermalCluster, initialize_thermal_cluster
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dtos import StudyDataSynthesis
from antarest.study.storage.rawstudy.model.filesystem.config.model import AreaConfig, EnrModelling, LinkConfig
from tests.helpers import explain_model_diff
from tests.study.dao.utils import save_area

ALL_FILTERS = list(FILTER_OPTIONS)

# Default district shipped by both FS templates and the DB factory.
DEFAULT_DISTRICT = District(
    id="all areas",
    name="All areas",
    output=False,
    comments="Spatial aggregates on all areas",
    apply_filter=DistrictApplyFilter.add_all,
)


class TestDatabaseSynthesisDao:
    def test_get_synthesis_empty_study(self, dao: StudyDao) -> None:
        synthesis = dao.get_synthesis()

        expected = StudyDataSynthesis.model_construct(
            study_id=dao.get_study_id(),
            version=dao.get_version(),
            areas={},
            districts={"all areas": DEFAULT_DISTRICT},
            bindings=[],
            enr_modelling=EnrModelling.CLUSTERS,
        )
        assert synthesis == expected, explain_model_diff(synthesis, expected)

    def test_get_synthesis_with_areas_and_clusters(self, dao: StudyDao) -> None:
        version = dao.get_version()

        save_area(dao, "France")
        save_area(dao, "Germany")

        dao.save_thermals({"france": [ThermalCluster(id="coal_plant", name="Coal Plant")]})
        dao.save_renewable("france", RenewableCluster(id="wind_farm", name="Wind Farm"))
        dao.save_st_storages({"germany": [STStorage(id="battery", name="Battery")]})

        synthesis = dao.get_synthesis()

        expected_thermal = ThermalCluster(id="coal_plant", name="Coal Plant")
        initialize_thermal_cluster(expected_thermal, version)
        expected_storage = STStorage(id="battery", name="Battery")
        initialize_st_storage(expected_storage, version)

        assert synthesis.areas == {
            "france": AreaConfig(
                name="France",
                links={},
                thermals=[expected_thermal],
                renewables=[RenewableCluster(id="wind_farm", name="Wind Farm")],
                filters_synthesis=ALL_FILTERS,
                filters_year=ALL_FILTERS,
            ),
            "germany": AreaConfig(
                name="Germany",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=ALL_FILTERS,
                filters_year=ALL_FILTERS,
                st_storages=[expected_storage],
            ),
        }

    def test_get_synthesis_with_links(self, dao: StudyDao) -> None:

        save_area(dao, "France")
        save_area(dao, "Germany")

        link = Link(area1="france", area2="germany")
        dao.save_links([link])

        synthesis = dao.get_synthesis()

        assert synthesis.areas == {
            "france": AreaConfig(
                name="France",
                links={"germany": LinkConfig(filters_synthesis=ALL_FILTERS, filters_year=ALL_FILTERS)},
                thermals=[],
                renewables=[],
                filters_synthesis=ALL_FILTERS,
                filters_year=ALL_FILTERS,
            ),
            "germany": AreaConfig(
                name="Germany",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=ALL_FILTERS,
                filters_year=ALL_FILTERS,
            ),
        }

    def test_get_synthesis_with_districts(self, dao: StudyDao) -> None:
        save_area(dao, "France")
        dao.save_district(District(id="north", name="North", add_areas=["france"]))
        dao.save_district(District(id="south", name="South"))

        synthesis = dao.get_synthesis()

        assert synthesis.districts == {
            "all areas": DEFAULT_DISTRICT,
            "north": District(id="north", name="North", add_areas=["france"]),
            "south": District(id="south", name="South"),
        }

    def test_get_synthesis_with_area_filters(self, dao: StudyDao) -> None:

        save_area(dao, "France")
        dao.save_area_properties("france", AreaProperties(filter_synthesis={"hourly", "daily"}))

        synthesis = dao.get_synthesis()

        assert synthesis.areas == {
            "france": AreaConfig(
                name="France",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=["hourly", "daily"],
                filters_year=ALL_FILTERS,
            ),
        }

    def test_get_synthesis_enr_modelling(self, dao: StudyDao) -> None:

        dao.save_advanced_parameters(
            AdvancedParameters(renewable_generation_modelling=RenewableGenerationModeling.AGGREGATED)
        )

        synthesis = dao.get_synthesis()
        assert synthesis.enr_modelling == EnrModelling.AGGREGATED

    def test_get_synthesis_bindings_empty_for_db(self, dao: StudyDao) -> None:
        synthesis = dao.get_synthesis()
        assert synthesis.bindings == []

    def test_get_synthesis_via_read_only_adapter(self, dao: StudyDao) -> None:
        save_area(dao, "Spain")

        read_only = dao.read_only()
        synthesis = read_only.get_synthesis()

        assert synthesis.areas == {
            "spain": AreaConfig(
                name="Spain",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=ALL_FILTERS,
                filters_year=ALL_FILTERS,
            ),
        }
