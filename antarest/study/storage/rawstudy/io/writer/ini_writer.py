import ast
from configparser import RawConfigParser
from pathlib import Path
from typing import List, Optional

from antarest.core.custom_types import JSON


class IniConfigParser(RawConfigParser):
    def __init__(self, special_keys: Optional[List[str]] = None) -> None:
        super().__init__()
        self.special_keys = special_keys

    def optionxform(self, optionstr: str) -> str:
        return optionstr

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
            value = delimiter + str(value).replace("\n", "\n\t")
        else:
            value = ""
        fp.write("{}{}\n".format(key, value))

    def _write_section(  # type:ignore
        self,
        fp,
        section_name,
        section_items,
        delimiter,
    ) -> None:
        """Write a single section to the specified `fp'."""
        fp.write("[{}]\n".format(section_name))
        for key, value in section_items:
            if (
                self.special_keys
                and key in self.special_keys
                and isinstance(ast.literal_eval(value), list)
            ):
                for sub_value in ast.literal_eval(value):
                    self._write_line(
                        delimiter, fp, key, section_name, sub_value
                    )
            else:
                self._write_line(delimiter, fp, key, section_name, value)
        fp.write("\n")


class IniWriter:
    """
    Standard .ini writer
    """

    def __init__(self, special_keys: Optional[List[str]] = None):
        self.special_keys = special_keys

    def write(self, data: JSON, path: Path) -> None:
        """
        Write .ini file fro json content
        Args:
            data: json content
            path: .ini file

        Returns:

        """
        config_parser = IniConfigParser(special_keys=self.special_keys)
        config_parser.read_dict(data)
        config_parser.write(path.open("w"))
