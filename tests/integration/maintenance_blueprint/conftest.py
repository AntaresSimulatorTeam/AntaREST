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

"""Fixtures for maintenance integration tests."""

import typing as t
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import StaticPool, create_engine, text
from sqlalchemy.engine.base import Engine

from antarest.core.config import InternalMatrixFormat
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.dbmodel import Base
from antarest.matrixstore.repository import MatrixContentRepository, MatrixDataSetRepository, MatrixRepository
from antarest.matrixstore.service import MatrixService


@pytest.fixture(name="db_engine")
def db_engine_fixture() -> t.Generator[Engine, None, None]:
    """Create an in-memory SQLite database engine for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON"))
        conn.commit()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(name="db_middleware")
def db_middleware_fixture(db_engine: Engine) -> t.Generator[DBSessionMiddleware, None, None]:
    """Set up database session middleware."""
    yield DBSessionMiddleware(
        None,
        custom_engine=db_engine,
        session_args={"autocommit": False, "autoflush": False},
    )


@pytest.fixture(name="matrix_content_repo")
def matrix_content_repo_fixture(tmp_path: Path) -> MatrixContentRepository:
    """Create a MatrixContentRepository for testing."""
    return MatrixContentRepository(tmp_path / "matrices", format=InternalMatrixFormat.TSV)


@pytest.fixture(name="matrix_service")
def matrix_service_fixture(
    db_middleware: DBSessionMiddleware,
    matrix_content_repo: MatrixContentRepository,
) -> MatrixService:
    """Create a real MatrixService with database support."""
    return MatrixService(
        repo=MatrixRepository(),
        repo_dataset=MatrixDataSetRepository(),
        matrix_content_repository=matrix_content_repo,
        file_transfer_manager=Mock(),
        task_service=Mock(),
        config=Mock(),
        user_service=Mock(),
    )
