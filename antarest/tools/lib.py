import json
import requests
from pathlib import Path
from typing import List, Optional

from requests import Session

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.model import (
    CommandDTO,
    GenerationResultInfoDTO,
)
from antarest.study.storage.variantstudy.model.command.common import CommandName


class CLIVariantManager:
    def __init__(
        self,
        host: Optional[str] = None,
        token: Optional[str] = None,
        session: Optional[Session] = None,
    ):
        self.session = session or requests.session()
        self.host = host
        if session is None and host is None:
            raise ValueError("Missing either session or host")
        if token is not None:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def parse_commands(self, file: Path) -> List[CommandDTO]:
        with open(file, "r") as fh:
            json_commands = json.load(fh)

        commands: List[CommandDTO] = []
        for command in json_commands:
            commands.append(CommandDTO.parse_obj(command))

        return commands

    def apply_commands(
        self,
        study_id: str,
        commands: List[CommandDTO],
    ) -> GenerationResultInfoDTO:
        study = self.session.get(
            self.build_url(f"/v1/studies/{study_id}")
        ).json()
        assert study is not None

        res = self.session.post(
            self.build_url(f"/v1/studies/{study_id}/commands"),
            json=[command.dict() for command in commands],
        )
        assert res.status_code == 200

        res = self.session.put(
            self.build_url(f"/v1/studies/{study_id}/generate?denormalize=true")
        )
        assert res.status_code == 200
        return GenerationResultInfoDTO.parse_obj(res.json())

    def build_url(self, url: str) -> str:
        if self.host is not None:
            return f"{self.host}/{url}"
        return url


def extract_commands(study: FileStudy) -> List[CommandDTO]:
    study_tree = study.tree
    study_config = study.config
    study_commands: List[CommandDTO] = []
    links_commands: List[CommandDTO] = []
    for area_id in study_config.areas:
        area = study_config.areas[area_id]
        area_command = CommandDTO(
            action=CommandName.CREATE_AREA,
            args={
                "area_name": area.name
            }
        )
        study_commands.append(area_command)
        links_data = study_tree.get(["input", "links", area_id, "properties.ini"])
        for link in area.links:
            link_command = CommandDTO(
                action=CommandName.CREATE_LINK,
                args={
                    "area1": area_id,
                    "area2": link,
                    "parameters": {},
                    "series": [],
                }
            )
            link_data = links_data.get(link)
            link_config_command = CommandDTO(
                action=CommandName.UPDATE_CONFIG,
                args={
                    "target": f"input/links/{area_id}/properties/{link}",
                    "data": link_data
                }
            )
            links_commands.append(link_command)
            links_commands.append()
        for thermal in area.thermals:
            CommandDTO(
                action=CommandName.
            )

    study_commands += links_commands
    return study_commands
