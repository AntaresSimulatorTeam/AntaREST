from pathlib import Path
from typing import List, Dict, Any

from antarest.core.config import Config
from antarest.core.logging.utils import configure_logger
from antarest.core.utils.utils import get_local_path
from antarest.utils import (
    Module,
    init_db,
    create_watcher,
    create_matrix_gc,
    create_archive_worker,
)


class SingletonServices:
    def __init__(self, config_file: Path, services_list: List[Module]) -> None:
        self.services_list = self._init(config_file, services_list)

    @staticmethod
    def _init(
        config_file: Path, services_list: List[Module]
    ) -> Dict[Module, Any]:
        res = get_local_path() / "resources"
        config = Config.from_yaml_file(res=res, file=config_file)
        init_db(config_file, config, False, None)
        configure_logger(config)

        services: Dict[Module, Any] = {}

        if Module.WATCHER in services_list:
            watcher = create_watcher(config=config, application=None)
            services[Module.WATCHER] = watcher

        if Module.MATRIX_GC in services_list:
            matrix_gc = create_matrix_gc(config=config, application=None)
            services[Module.MATRIX_GC] = matrix_gc

        if Module.ARCHIVE_WORKER in services_list:
            worker = create_archive_worker(config, "test")
            services[Module.ARCHIVE_WORKER] = worker

        return services

    def start(self) -> None:
        for service in self.services_list:
            self.services_list[service].start(threaded=True)
