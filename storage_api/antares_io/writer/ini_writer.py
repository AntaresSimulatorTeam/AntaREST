from configparser import ConfigParser, RawConfigParser
from pathlib import Path

from storage_api.custom_types import JSON


class IniWriter:
    def write(self, data: JSON, path: Path) -> None:
        config_parser = IniConfigParser()
        config_parser.read_dict(data)
        config_parser.write(path.open("w"))


class IniConfigParser(RawConfigParser):
    def optionxform(self, optionstr: str) -> str:
        return optionstr
