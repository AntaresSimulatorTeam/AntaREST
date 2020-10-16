import configparser
from pathlib import Path
from typing import Optional, Union

from api_iso_antares.custom_types import JSON, ELEMENT


class IniReader:
    @staticmethod
    def _parse_bool(value: str) -> Optional[bool]:
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
    def _parse_value(value: str) -> ELEMENT:
        parsed: Union[str, int, float, bool, None] = IniReader._parse_bool(
            value
        )
        parsed = parsed if parsed is not None else IniReader._parse_int(value)
        parsed = (
            parsed if parsed is not None else IniReader._parse_float(value)
        )
        return parsed if parsed is not None else value

    @staticmethod
    def _parse_json(json: configparser.SectionProxy) -> JSON:
        return {
            key: IniReader._parse_value(value) for key, value in json.items()
        }

    @staticmethod
    def read(path: Path) -> JSON:
        config = IniConfigParser()
        config.read(path)

        return {
            key: IniReader._parse_json(config[key])
            for key in config
            if key != "DEFAULT"
        }


class IniConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr: str) -> str:
        return optionstr
