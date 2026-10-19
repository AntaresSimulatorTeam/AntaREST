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

from sqlalchemy import Column, ForeignKeyConstraint, PrimaryKeyConstraint, String, Table

from antarest.core.utils.sql_utils import enum_col
from antarest.dbmodel import Base
from antarest.study.business.model.gems.catalog import GemsAggregationOperator
from antarest.study.dao.database.models import study_data_id_col

GEMS_CATALOGS_TABLE = Table(
    "gems_catalogs",
    Base.metadata,
    study_data_id_col(),
    Column("id", String(255), primary_key=True),
    Column("taxonomy", String(255), nullable=False),
    Column("location", String(255), nullable=False),
    ForeignKeyConstraint(
        ["study_data_id"], ["study_data.study_data_id"], name="fk_gems_catalogs_study_data", ondelete="CASCADE"
    ),
    ForeignKeyConstraint(
        ["study_data_id", "location"],
        ["gems_taxonomy_categories.study_data_id", "gems_taxonomy_categories.id"],
        name="fk_gems_catalogs_location",
    ),
    ForeignKeyConstraint(
        ["study_data_id", "taxonomy"],
        ["gems_taxonomy_metadata.study_data_id", "gems_taxonomy_metadata.id"],
        name="fk_gems_catalogs_taxonomy",
    ),
    PrimaryKeyConstraint("study_data_id", "id", name="pk_gems_catalogs"),
)


GEMS_CATALOG_METRICS_TABLE = Table(
    "gems_catalog_metrics",
    Base.metadata,
    study_data_id_col(),
    Column("catalog_id", String(255), primary_key=True),
    Column("id", String(255), primary_key=True),
    Column("terms_operator", enum_col(GemsAggregationOperator, name="gems_aggregation_operator"), nullable=False),
    Column("time_operator", enum_col(GemsAggregationOperator, name="gems_aggregation_operator"), nullable=False),
    # Nested definitions remain JSON. SQL NULL means omitted; JSON null means explicitly null.
    Column("terms", String(), nullable=True),
    Column("breakdown", String(), nullable=True),
    Column("filter", String(), nullable=True),
    ForeignKeyConstraint(
        ["study_data_id", "catalog_id"],
        ["gems_catalogs.study_data_id", "gems_catalogs.id"],
        name="fk_gems_catalog_metrics_catalog",
        ondelete="CASCADE",
    ),
    PrimaryKeyConstraint("study_data_id", "catalog_id", "id", name="pk_gems_catalog_metrics"),
)
