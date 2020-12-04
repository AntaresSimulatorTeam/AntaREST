import configparser
from abc import ABC
from pathlib import Path
from typing import List, Optional, Union, cast, Type, Dict, Any

from api_iso_antares.custom_types import JSON, ELEMENT, SUB_JSON
from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.inode import INode


class IniFileNode(INode, ABC):
    def __init__(self, config: Config, types: Optional[Dict[str, Any]] = None):
        self.path = config.path
        self.types = types or dict()

    def get(self, url: List[str]) -> SUB_JSON:
        json = self.to_json()
        self.validate(json)
        for key in url:
            json = json[key]
        return cast(SUB_JSON, json)

    def to_json(self) -> JSON:
        return IniConfigParser().parse(self.path)

    def validate(self, data: JSON) -> None:
        for section, params in self.types.items():
            if section not in data:
                raise ValueError(
                    f"section {section} not in {self.__class__.__name__}"
                )
            sub_data = data[section]
            for param, typing in params.items():
                if param not in sub_data:
                    raise ValueError(
                        f"param {param} of section {section} not in {self.__class__.__name__}"
                    )
                if not isinstance(sub_data[param], typing):
                    raise ValueError(
                        f"param {param} of section {section} in {self.__class__.__name__} not good type"
                    )


class IniConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr: str) -> str:
        return optionstr

    @staticmethod
    def _parse_bool(value: str) -> Optional[bool]:
        value = value.lower()
        return bool(value == "true") if value in ["true", "false"] else None

    @staticmethod
    def _parse_int(value: str) -> Optional[int]:
        try:
            return int(value)
        except ValueError:
            return None

    @staticmethod
    def _parse_float(value: str) -> Optional[float]:
        try:
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def parse_value(value: str) -> ELEMENT:
        parsed: Union[
            str, int, float, bool, None
        ] = IniConfigParser._parse_bool(value)
        parsed = (
            parsed if parsed is not None else IniConfigParser._parse_int(value)
        )
        parsed = (
            parsed
            if parsed is not None
            else IniConfigParser._parse_float(value)
        )
        return parsed if parsed is not None else value

    @staticmethod
    def _parse_json(json: configparser.SectionProxy) -> JSON:
        return {
            key: IniConfigParser.parse_value(value)
            for key, value in json.items()
        }

    def parse(self, path: Path) -> JSON:
        IniConfigParser.read(self, path)
        config = IniConfigParser()
        config.read(path)

        return {
            key: IniConfigParser._parse_json(config[key])
            for key in config
            if key != "DEFAULT"
        }
