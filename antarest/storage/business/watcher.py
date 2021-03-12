from antarest.common.config import Config
from antarest.storage.service import StorageService


class Watcher:
    def __init__(self, config: Config, service: StorageService):
        self.service = service
        self.config = config

    def init(self):
        pass
