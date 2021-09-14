import configparser
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union

from antarest.core.custom_types import ELEMENT, JSON


class IReader(ABC):
    """
    Init file Reader interface
    """

    @abstractmethod
    def read(self, path: Path) -> JSON:
        """
        Parse .ini file to json
        Args:
            path: .ini file

        Returns: json content

        """
        raise NotImplementedError()


class IniReader(IReader):
    """
    Standard .ini file reader. Use for general purpose.
    """

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
            key: IniReader.parse_value(value) for key, value in json.items()
        }

    def read(self, path: Path) -> JSON:
        config = IniConfigParser()
        config.read(path)

        return {
            key: IniReader._parse_json(config[key])
            for key in config
            if key != "DEFAULT"
        }


class IniConfigParser(configparser.RawConfigParser):
    def optionxform(self, optionstr: str) -> str:
        return optionstr


class MultipleSameKeysIniReader(IReader):
    """
    Custom .ini reader for inputs/sets.ini file.
    This file has format :
    ``` python
    [chap]
    + = areaA
    + = areaB
    ```

    multikey is not compatible with standard .ini readers
    """

    def __init__(self, special_keys: Optional[List[str]] = None) -> None:
        self.special_keys = special_keys or []
        super().__init__()

    @staticmethod
    def fetch_cleaned_lines(path: Path) -> List[str]:
        return [l for l in path.read_text().split("\n") if l.strip() != ""]

    def read(self, path: Path) -> JSON:
        data: JSON = dict()
        curr_part = ""
        lines = MultipleSameKeysIniReader.fetch_cleaned_lines(path)

        for l in lines:
            line = l.strip()
            regex = re.search("^\[(.*)\]$", line)
            if regex:
                curr_part = regex.group(1)
                data[curr_part] = dict()
            else:
                elements = re.split("\s+=\s*", line)
                key = elements[0]
                value = None
                if len(elements) == 2:
                    value = IniReader.parse_value(elements[1].strip())
                if key not in data[curr_part]:
                    if key in self.special_keys:
                        data[curr_part][key] = [value]
                    else:
                        data[curr_part][key] = value
                else:
                    if not isinstance(data[curr_part][key], list):
                        data[curr_part][key] = [data[curr_part][key]]
                    data[curr_part][key].append(value)

        return data
