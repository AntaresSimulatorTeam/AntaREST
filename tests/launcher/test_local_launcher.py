from pathlib import Path
from unittest.mock import Mock, call
from uuid import uuid4

import pytest
from sqlalchemy import create_engine

from antarest.core.config import Config
from antarest.core.persistence import Base
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.launcher.adapters.local_launcher.local_launcher import (
    LocalLauncher,
)
from antarest.launcher.model import JobStatus


@pytest.mark.unit_test
def test_compute(tmp_path: Path):
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )
    storage_service = Mock()
    local_launcher = LocalLauncher(
        Config(),
        storage_service=storage_service,
        callbacks=Mock(),
        event_bus=Mock(),
    )

    uuid = uuid4()
    local_launcher.job_id_to_study_id = {
        str(uuid): ("study-id", tmp_path / "run", Mock())
    }
    storage_service.import_output.return_value = "some output"
    local_launcher._compute(
        antares_solver_path="echo",
        study_uuid="study-id",
        uuid=uuid,
        launcher_parameters=None,
    )

    local_launcher.callbacks.update_status.assert_has_calls(
        [
            call(str(uuid), JobStatus.RUNNING, None, None),
            call(str(uuid), JobStatus.SUCCESS, None, "some output"),
        ]
    )
