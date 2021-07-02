from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends
from starlette.testclient import TestClient

from antarest.common.config import Config
from antarest.common.utils.file_transfer import FileTransferManager


def create_app() -> FastAPI:
    app = FastAPI(title=__name__)
    return app


def test_file_request():
    app = create_app()
    ftm = FileTransferManager.get_instance(Config())

    @app.get("/dummy")
    def dummy_endpoint(tmppath: Path = Depends(ftm.request_tmp_file)):
        tmppath.touch()
        assert tmppath.exists()
        return tmppath

    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/dummy")
    tmppath = res.json()
    assert tmppath is not None
    assert not Path(tmppath).exists()
