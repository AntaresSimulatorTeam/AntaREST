import logging
import time
from pathlib import Path
from typing import Dict, List

from antarest.core.config import Config
from antarest.core.interfaces.service import IService
from antarest.core.logging.utils import configure_logger
from antarest.core.utils.utils import get_local_path
from antarest.study.storage.auto_archive_service import AutoArchiveService
from antarest.utils import (
    Module,
    create_archive_worker,
    create_core_services,
    create_matrix_gc,
    create_simulator_worker,
    create_watcher,
    init_db,
)

logger = logging.getLogger(__name__)


class SingletonServices:
    def __init__(self, config_file: Path, services_list: List[Module]) -> None:
        self.services_list = self._init(config_file, services_list)

    @staticmethod
    def _init(
        config_file: Path, services_list: List[Module]
    ) -> Dict[Module, IService]:
        res = get_local_path() / "resources"
        config = Config.from_yaml_file(res=res, file=config_file)
        init_db(config_file, config, False, None)
        configure_logger(config)

        (
            cache,
            event_bus,
            task_service,
            ft_manager,
            login_service,
            matrix_service,
            study_service,
        ) = create_core_services(None, config)

        services: Dict[Module, IService] = {}

        if Module.WATCHER in services_list:
            watcher = create_watcher(
                config=config, application=None, study_service=study_service
            )
            services[Module.WATCHER] = watcher

        if Module.MATRIX_GC in services_list:
            matrix_gc = create_matrix_gc(
                config=config,
                application=None,
                study_service=study_service,
                matrix_service=matrix_service,
            )
            services[Module.MATRIX_GC] = matrix_gc

        if Module.ARCHIVE_WORKER in services_list:
            worker = create_archive_worker(config, "test", event_bus=event_bus)
            services[Module.ARCHIVE_WORKER] = worker

        if Module.SIMULATOR_WORKER in services_list:
            worker = create_simulator_worker(
                config, matrix_service=matrix_service, event_bus=event_bus
            )
            services[Module.SIMULATOR_WORKER] = worker

        if Module.AUTO_ARCHIVER in services_list:
            auto_archive_service = AutoArchiveService(study_service, config)
            services[Module.AUTO_ARCHIVER] = auto_archive_service

        return services

    def start(self) -> None:
        for service in self.services_list:
            self.services_list[service].start(threaded=True)

        self._loop()

    def _loop(self) -> None:
        while True:
            try:
                pass
            except Exception as e:
                logger.error(
                    "Unexpected error happened while processing service manager loop",
                    exc_info=e,
                )
            finally:
                time.sleep(2)
