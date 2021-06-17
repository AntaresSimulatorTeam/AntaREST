from configparser import RawConfigParser
from pathlib import Path

from antarest.common.custom_types import JSON


class IniWriter:
    """
    Standard .ini writer
    """

    def write(self, data: JSON, path: Path) -> None:
        """
        Write .ini file fro json content
        Args:
            data: json content
            path: .ini file

        Returns:

        """
        config_parser = IniConfigParser()
        config_parser.read_dict(data)
        config_parser.write(path.open("w"))


class IniConfigParser(RawConfigParser):
    def optionxform(self, optionstr: str) -> str:
        return optionstr
