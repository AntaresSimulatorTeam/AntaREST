from pathlib import Path

from antarest.common.config import Config
from antarest.login.model import Group
from antarest.storage.service import StorageService


class Watcher:
    def __init__(self, config: Config, service: StorageService):
        self.service = service
        self.config = config

    def init(self) -> None:
        for name, workspace in self.config["storage.workspaces"].items():
            path = Path(workspace["path"])
            groups = [Group(id=g) for g in workspace.get("groups", [])]

            for folder in path.iterdir():
                if (folder / "study.antares").exists():
                    self.service.create_study_from_watcher(
                        folder, name, groups
                    )
