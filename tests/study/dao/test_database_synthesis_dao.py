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
Unit tests for get_synthesis on the DAO layer (database backend).
"""

from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.business.model.config.advanced_parameters_model import (
    AdvancedParameters,
    RenewableGenerationModeling,
)
from antarest.study.business.model.district_model import District
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.sts_model import STStorage
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.storage.rawstudy.model.filesystem.config.model import EnrModelling


class TestDatabaseSynthesisDao:
    def test_get_synthesis_empty_study(self, db_dao: DatabaseStudyDao) -> None:
        """Synthesis of a study with no areas/links/etc. should return empty collections."""
        synthesis = db_dao.get_synthesis()

        assert synthesis.study_id == db_dao.get_study_id()
        assert synthesis.version == db_dao.get_version()
        assert synthesis.areas == {}
        assert synthesis.districts == {}
        assert synthesis.bindings == []
        assert synthesis.enr_modelling == EnrModelling.CLUSTERS

    def test_get_synthesis_with_areas_and_clusters(self, db_dao: DatabaseStudyDao) -> None:
        """Synthesis should include areas with their thermals, renewables, and st_storages."""
        dao = db_dao

        # Setup areas
        dao.save_area("France")
        dao.save_area("Germany")

        # Setup thermal cluster
        dao.save_thermal("france", ThermalCluster(id="coal_plant", name="Coal Plant"))
        # Setup renewable cluster
        dao.save_renewable("france", RenewableCluster(id="wind_farm", name="Wind Farm"))
        # Setup ST storage
        dao.save_st_storage("germany", STStorage(id="battery", name="Battery"))

        synthesis = dao.get_synthesis()

        assert "france" in synthesis.areas
        assert "germany" in synthesis.areas

        france = synthesis.areas["france"]
        assert france.name == "France"
        assert len(france.thermals) == 1
        assert france.thermals[0].id == "coal_plant"
        assert len(france.renewables) == 1
        assert france.renewables[0].id == "wind_farm"

        germany = synthesis.areas["germany"]
        assert germany.name == "Germany"
        assert len(germany.st_storages) == 1
        assert germany.st_storages[0].id == "battery"

    def test_get_synthesis_with_links(self, db_dao: DatabaseStudyDao) -> None:
        """Synthesis should include links organized by source area."""
        dao = db_dao

        dao.save_area("France")
        dao.save_area("Germany")

        link = Link(area1="france", area2="germany")
        dao.save_link(link)

        synthesis = dao.get_synthesis()

        # Links are stored under the alphabetically-first area
        france_links = synthesis.areas["france"].links
        assert "germany" in france_links
        # germany should have no outgoing links
        assert synthesis.areas["germany"].links == {}

    def test_get_synthesis_with_districts(self, db_dao: DatabaseStudyDao) -> None:
        """Synthesis should include districts keyed by ID."""
        dao = db_dao

        dao.save_area("France")
        dao.save_district(District(id="north", name="North", add_areas=["france"]))
        dao.save_district(District(id="south", name="South"))

        synthesis = dao.get_synthesis()

        assert "north" in synthesis.districts
        assert "south" in synthesis.districts
        assert synthesis.districts["north"].name == "North"
        assert synthesis.districts["south"].name == "South"

    def test_get_synthesis_with_area_filters(self, db_dao: DatabaseStudyDao) -> None:
        """Synthesis should reflect area filter properties."""
        dao = db_dao

        dao.save_area("France")
        dao.save_area_properties("france", AreaProperties(filter_synthesis={"hourly", "daily"}))

        synthesis = dao.get_synthesis()

        france = synthesis.areas["france"]
        assert france.filters_synthesis == ["hourly", "daily"]

    def test_get_synthesis_enr_modelling(self, db_dao: DatabaseStudyDao) -> None:
        """Synthesis should reflect the renewable generation modelling setting."""
        dao = db_dao

        dao.save_advanced_parameters(
            AdvancedParameters(renewable_generation_modelling=RenewableGenerationModeling.AGGREGATED)
        )

        synthesis = dao.get_synthesis()
        assert synthesis.enr_modelling == EnrModelling.AGGREGATED

    def test_get_synthesis_bindings_empty_for_db(self, db_dao: DatabaseStudyDao) -> None:
        """Constraints are not yet implemented for DB mode, so bindings should be empty."""
        synthesis = db_dao.get_synthesis()
        assert synthesis.bindings == []

    def test_get_synthesis_via_read_only_adapter(self, db_dao: DatabaseStudyDao) -> None:
        """get_synthesis should be available through the read-only adapter."""
        dao = db_dao
        dao.save_area("Spain")

        read_only = dao.read_only()
        synthesis = read_only.get_synthesis()

        assert "spain" in synthesis.areas
        assert synthesis.areas["spain"].name == "Spain"
