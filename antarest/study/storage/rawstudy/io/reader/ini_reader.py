import configparser
import contextlib
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union

from antarest.core.model import JSON, SUB_JSON


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
        return {"true": True, "false": False}.get(value.lower())

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
    def parse_value(value: str) -> SUB_JSON:
        def strict_bool(v):
            return {"true": True, "false": False}[v.lower()]

        for parser in [strict_bool, int, float]:
            with contextlib.suppress(KeyError, ValueError):
                return parser(value)
        return value

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


class SimpleKeyValueReader(IReader):
    """
    Standard .ini file reader. Use for general purpose.
    """

    @staticmethod
    def _parse_inf(value: str) -> Optional[str]:
        try:
            return "+Inf" if float(value) == float("inf") else None
        except ValueError:
            return None

    # noinspection PyProtectedMember
    @staticmethod
    def parse_value(value: str) -> SUB_JSON:
        parsed: Union[
            str, int, float, bool, None
        ] = SimpleKeyValueReader._parse_inf(value)
        parsed = parsed if parsed is not None else IniReader._parse_bool(value)
        parsed = parsed if parsed is not None else IniReader._parse_int(value)
        parsed = (
            parsed if parsed is not None else IniReader._parse_float(value)
        )
        return parsed if parsed is not None else value

    @staticmethod
    def _parse_json(json: JSON) -> JSON:
        return {
            key: SimpleKeyValueReader.parse_value(value)
            for key, value in json.items()
        }

    def read(self, path: Path) -> JSON:
        json = {}
        with open(path, "r") as fd:
            for line in fd:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=")
                    json[key.strip()] = value.strip()

        return self._parse_json(json)


class IniConfigParser(configparser.RawConfigParser):
    # noinspection SpellCheckingInspection
    def optionxform(self, optionstr: str) -> str:
        return optionstr


class MultipleSameKeysIniReader(IReader):
    """
    Custom .ini reader for inputs/sets.ini file.
    This file has format :
    ```python
    [chap]
    + = areaA
    + = areaB
    ```

    multikey is not compatible with standard .ini readers
    """

    def __init__(self, special_keys: Optional[List[str]] = None) -> None:
        self.special_keys = special_keys or []
        super().__init__()

    def read(self, path: Path) -> JSON:
        data: JSON = {}
        section = ""
        with path.open(encoding="utf-8") as lines:
            for line in lines:
                line = line.strip()
                if match := re.fullmatch(r"\[(.*)]", line):
                    section = match[1]
                    data[section] = {}
                elif "=" in line:
                    key, value = map(str.strip, line.split("=", 1))
                    value = IniReader.parse_value(value)
                    group = data[section]
                    if key in group:
                        if isinstance(group[key], list):
                            group[key].append(value)
                        else:
                            group[key] = [group[key], value]
                    elif key in self.special_keys:
                        group[key] = [value]
                    else:
                        group[key] = value

        return data
