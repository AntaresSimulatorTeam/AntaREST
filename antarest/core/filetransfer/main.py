from fastapi import FastAPI

from antarest.core.config import Config
from antarest.core.filetransfer.repository import FileDownloadRepository
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.filetransfer.web import create_file_transfer_api
from antarest.core.interfaces.eventbus import IEventBus


def build_filetransfer_service(
    application: FastAPI, event_bus: IEventBus, config: Config
) -> FileTransferManager:
    ftm = FileTransferManager(
        repository=FileDownloadRepository(), event_bus=event_bus, config=config
    )

    application.include_router(create_file_transfer_api(ftm, config))
    return ftm
