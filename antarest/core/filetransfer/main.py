from fastapi import FastAPI

from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.filetransfer.web import create_file_transfer_api


def build_filetransfer_service(
    application: FastAPI, config: Config
) -> FileTransferManager:
    ftm = FileTransferManager(config)

    application.include_router(create_file_transfer_api(ftm, config))
    return ftm
