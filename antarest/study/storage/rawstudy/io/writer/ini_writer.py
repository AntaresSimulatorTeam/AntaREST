import ast
from configparser import RawConfigParser
from pathlib import Path
from typing import Any, List, Optional

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.io.reader import IniReader


class IniConfigParser(RawConfigParser):
    def __init__(self, special_keys: Optional[List[str]] = None) -> None:
        super().__init__()
        self.special_keys = special_keys

    # noinspection SpellCheckingInspection
    def optionxform(self, optionstr: str) -> str:
        return optionstr

    @staticmethod
    def format_value(value: Any) -> Any:
        parsed_value = IniReader.parse_value(value)
        if isinstance(parsed_value, bool):
            return str(parsed_value).lower()
        elif isinstance(parsed_value, float):
            return "%.6f" % parsed_value
        return value

    def _write_line(  # type:ignore
        self,
        delimiter,
        fp,
        key,
        section_name,
        value,
    ) -> None:
        value = self._interpolation.before_write(  # type:ignore
            self, section_name, key, value
        )
        if value is not None or not self._allow_no_value:  # type:ignore
            # value = IniConfigParser.format_value(value)
            value = delimiter + str(value).replace("\n", "\n\t")
        else:
            value = ""
        fp.write(f"{key}{value}\n")

    def _write_section(  # type:ignore
        self,
        fp,
        section_name,
        section_items,
        delimiter,
    ) -> None:
        """Write a single section to the specified `fp`."""
        fp.write(f"[{section_name}]\n")
        for key, value in section_items:
            if self.special_keys and key in self.special_keys and isinstance(ast.literal_eval(value), list):
                for sub_value in ast.literal_eval(value):
                    self._write_line(delimiter, fp, key, section_name, sub_value)
            else:
                self._write_line(delimiter, fp, key, section_name, value)
        fp.write("\n")


class IniWriter:
    """
    Standard INI writer.
    """

    def __init__(self, special_keys: Optional[List[str]] = None):
        self.special_keys = special_keys

    def write(self, data: JSON, path: Path) -> None:
        """
        Write `.ini` file from JSON content

        Args:
            data: JSON content.
            path: path to `.ini` file.
        """
        config_parser = IniConfigParser(special_keys=self.special_keys)
        config_parser.read_dict(data)
        with path.open("w") as fp:
            config_parser.write(fp)


class SimpleKeyValueWriter(IniWriter):
    """
    Simple key/value INI writer.
    """

    def write(self, data: JSON, path: Path) -> None:
        """
        Write `.ini` file from JSON content

        Args:
            data: JSON content.
            path: path to `.ini` file.
        """
        with path.open("w") as fp:
            for key, value in data.items():
                if value is not None:
                    fp.write(f"{key}={value}\n")
