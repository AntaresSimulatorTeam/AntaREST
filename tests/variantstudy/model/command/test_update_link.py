# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import LinksParametersTsGeneration, RawStudy
from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.update_link import UpdateLink
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.db_statement_recorder import DBStatementRecorder
from tests.helpers import with_db_context


class TestUpdateLink:
    @with_db_context
    def test_apply(self, empty_study: FileStudy, command_context: CommandContext):
        # =============================
        #  SET UP
        # =============================

        study_version = empty_study.config.version
        study_path = empty_study.config.study_path
        study_id = empty_study.config.study_id
        raw_study = RawStudy(id=study_id, version=str(study_version), path=str(study_path))
        db.session.add(raw_study)
        db.session.commit()

        area1_id = "area1"
        area2_id = "area2"

        CreateArea.model_validate(
            {"area_name": area1_id, "command_context": command_context, "study_version": study_version}
        ).apply(empty_study)

        CreateArea.model_validate(
            {"area_name": area2_id, "command_context": command_context, "study_version": study_version}
        ).apply(empty_study)

        # =============================
        #  NOMINAL CASES
        # =============================

        # Link creation
        parameters = {
            "hurdles-cost": True,
            "asset-type": "dc",
            "link-width": 12,
            "colorr": 120,
            "unit_count": 56,
            "law_planned": "geometric",
        }

        command_parameters = {
            "area1": area2_id,
            "area2": area1_id,
            "command_context": command_context,
            "study_version": study_version,
        }
        creation_parameters = {"parameters": parameters, **command_parameters}
        CreateLink.model_validate(creation_parameters).apply(study_data=empty_study)

        # Updating an Ini property
        new_parameters = {"colorb": 35}
        update_parameters = {"parameters": new_parameters, **command_parameters}

        with DBStatementRecorder(db.session.bind) as db_recorder:
            UpdateLink.model_validate(update_parameters).apply(study_data=empty_study)
            # We shouldn't call the DB as no DB parameter were given
            assert len(db_recorder.sql_statements) == 0

        # Asserts the ini file is well modified (new value + old values unmodified)
        link = IniReader()
        ini_path = study_path / "input" / "links" / area1_id / "properties.ini"
        link_data = link.read(ini_path)
        assert link_data[area2_id]["hurdles-cost"] == parameters["hurdles-cost"]
        assert link_data[area2_id]["asset-type"] == parameters["asset-type"]
        assert link_data[area2_id]["colorb"] == new_parameters["colorb"]

        # Updating a DB property
        new_parameters = {"nominal_capacity": 111}
        update_parameters = {"parameters": new_parameters, **command_parameters}
        # Removes the ini file to show we don't need it as we're only updating the DB
        ini_path.unlink()

        # Checks the DB state. Old properties should remain the same and the new one should be updated
        ts_gen_properties = (
            db.session.query(LinksParametersTsGeneration)
            .filter_by(study_id=study_id, area_from=area1_id, area_to=area2_id)
            .all()
        )
        assert len(ts_gen_properties) == 1
        link_ts_gen_props = ts_gen_properties[0]
        assert link_ts_gen_props.unit_count == parameters["unit_count"]
        assert link_ts_gen_props.law_planned == parameters["law_planned"]
        assert link_ts_gen_props.nominal_capacity == new_parameters["nominal_capacity"]
