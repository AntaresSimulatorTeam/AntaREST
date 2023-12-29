import typing as t
from abc import ABC, abstractmethod
from pathlib import Path

from antarest.core.model import JSON, SUB_JSON


def convert_value(value: str) -> t.Union[str, int, float, bool]:
    """Convert value to the appropriate type for JSON."""

    try:
        # Infinity values are not supported by JSON, so we use a string instead.
        mapping = {"true": True, "false": False, "+inf": "+Inf", "-inf": "-Inf", "inf": "+Inf"}
        return t.cast(t.Union[str, int, float, bool], mapping[value.lower()])
    except KeyError:
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value


def convert_obj(item: t.Any) -> SUB_JSON:
    """Convert object to the appropriate type for JSON (scalar, dictionary or list)."""

    if isinstance(item, dict):
        return {key: convert_obj(value) for key, value in item.items()}
    elif isinstance(item, list):
        return [convert_obj(value) for value in item]
    else:
        return convert_value(item)


class IReader(ABC):
    """
    Init file Reader interface
    """

    @abstractmethod
    def read(self, path: t.Any) -> JSON:
        """
        Parse `.ini` file to json object.

        Args:
            path: Path to `.ini` file or file-like object.

        Returns:
            Dictionary of parsed `.ini` file which can be converted to JSON.
        """
        raise NotImplementedError()


class IniReader(IReader):
    """
    Common `.ini` file reader. Use for general purpose.
    """

    def __init__(self, special_keys: t.Sequence[str] = (), section_name: str = "settings") -> None:
        super().__init__()

        # Default section name to use if `.ini` file has no section.
        self._special_keys = set(special_keys)

        # List of keys which should be parsed as list.
        self._section_name = section_name

    def __repr__(self) -> str:  # pragma: no cover
        """Return a string representation of the object."""
        cls = self.__class__.__name__
        # use getattr() to make sure that the attributes are defined
        special_keys = tuple(getattr(self, "_special_keys", ()))
        section_name = getattr(self, "_section_name", "settings")
        return f"{cls}(special_keys={special_keys!r}, section_name={section_name!r})"

    def read(self, path: t.Any) -> JSON:
        if isinstance(path, (Path, str)):
            try:
                with open(path, mode="r", encoding="utf-8") as f:
                    sections = self._parse_ini_file(f)
            except UnicodeDecodeError:
                # On windows, `.ini` files may use "cp1252" encoding
                with open(path, mode="r", encoding="cp1252") as f:
                    sections = self._parse_ini_file(f)
            except FileNotFoundError:
                # If the file is missing, an empty dictionary is returned.
                # This is required tp mimic the behavior of `configparser.ConfigParser`.
                return {}

        elif hasattr(path, "read"):
            with path:
                sections = self._parse_ini_file(path)

        else:  # pragma: no cover
            raise TypeError(repr(type(path)))

        return t.cast(JSON, convert_obj(sections))

    def _parse_ini_file(self, ini_file: t.TextIO) -> JSON:
        """
        Parse `.ini` file to JSON object.

        The following parsing rules are applied:

        - If the file has no section, then the default section name is used.
          This case is required to parse Xpansion `user/expansion/settings.ini` files
          (using `SimpleKeyValueReader` subclass).

        - If the file has duplicate sections, then the values are merged.
          This case is required when the end-user produced an ill-formed `.ini` file.
          This ensures the parsing is robust even if some values may be lost.

        - If a section has duplicate keys, then the values are merged.
          This case is required, for instance, to parse `settings/generaldata.ini` files which
          has duplicate keys like "playlist_year_weight", "playlist_year +", "playlist_year -",
          "select_var -", "select_var +", in the `[playlist]` section.
          In this case, duplicate keys must be declared in the `special_keys` argument,
          to parse them as list.

        - If a section has no key, then an empty dictionary is returned.
          This case is required to parse `input/hydro/prepro/correlation.ini` files.

        - If a section name has square brackets, then they are preserved.
          This case is required to parse `input/hydro/allocation/{area-id}.ini` files.

        Args:
            ini_file: file or file-like object.

        Returns:
            Dictionary of parsed `.ini` file which can be converted to JSON.
        """
        # NOTE: This algorithm is 1.93x faster than configparser.ConfigParser
        sections: t.Dict[str, t.Dict[str, t.Any]] = {}
        section_name = self._section_name

        for line in ini_file:
            line = line.strip()
            if not line or line.startswith(";") or line.startswith("#"):
                continue
            elif line.startswith("["):
                section_name = line[1:-1]
                sections.setdefault(section_name, {})
            elif "=" in line:
                key, value = map(str.strip, line.split("=", 1))
                section = sections.setdefault(section_name, {})
                if key in self._special_keys:
                    section.setdefault(key, []).append(value)
                else:
                    section[key] = value
            else:
                raise ValueError(f"☠☠☠ Invalid line: {line!r}")

        return sections


class SimpleKeyValueReader(IniReader):
    """
    Simple INI reader for "settings.ini" file which has no section.
    """

    def read(self, path: t.Any) -> JSON:
        """
        Parse `.ini` file which has no section to JSON object.

        This class is required to parse Xpansion `user/expansion/settings.ini` files.

        Args:
            path: Path to `.ini` file or file-like object.

        Returns:
            Dictionary of parsed key/value pairs.
        """
        sections = super().read(path)
        obj = t.cast(t.Mapping[str, JSON], sections)
        return obj[self._section_name]


class MultipleSameKeysIniReader(IniReader):
    """
    Custom `.ini` reader for `.ini` files which have duplicate keys in a section.

    This class is required, to parse `settings/generaldata.ini` files which
    has duplicate keys like "playlist_year_weight", "playlist_year +", "playlist_year -",
    "select_var -", "select_var +", in the `[playlist]` section.

    For instance::

        [playlist]
        playlist_reset = false
        playlist_year + = 6
        playlist_year + = 8
        playlist_year + = 13

    It is also required to parse `input/areas/sets.ini` files which have keys like "+" or "-".

    For instance::

        [all areas]
        caption = All areas
        comments = Spatial aggregates on all areas
        + = east
        + = west

    This class is not compatible with standard `.ini` readers.
    """
