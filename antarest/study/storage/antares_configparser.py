import configparser
from typing import Any, Dict, Union, Optional


def _convert_value(value: Any) -> str:
    """
    Convert a value to a string using the specific format of Antares INI files.

    - strings are preserved,
    - ``None`` is converted to an empty string,
    - booleans are converted to "true"/"false" in lower case.
    - numbers are converted to strings using the :class:`str` function.
    """
    if value is None:
        return ""
    elif value is True or value is False:
        return str(value).lower()
    else:
        return str(value)


class AntaresSectionProxy(configparser.SectionProxy):
    """
    This class extends the :class:`configparser.SectionProxy` class in order
    to store strings or other types of values by converting them according
    to the rules of Antares INI files.
    """

    def __repr__(self) -> str:
        """String representation of the section proxy used for debug."""
        cls = self.__class__.__name__
        return f"<{cls}: {self._name}>"

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Sets the value of the specified key in the section.
        """
        super().__setitem__(key, _convert_value(value))


class AntaresConfigParser(configparser.RawConfigParser):
    """
    This class extends the :class:`configparser.RawConfigParser` class in order
    to store strings or other types of values by converting them according
    to the rules of Antares INI files.
    """

    _proxies: Dict[str, AntaresSectionProxy]
    _sections: Dict[str, Optional[Union[bool, int, float, str]]]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        super().__init__(*args, **kwargs)
        self._proxies[self.default_section] = AntaresSectionProxy(
            self, self.default_section
        )

    def add_section(self, section: str) -> None:
        super().add_section(section)
        self._proxies[section] = AntaresSectionProxy(self, section)

    def set(self, section: str, option: str, value: Any = None) -> None:
        super().set(section, option, _convert_value(value))

    def _read(self, fp, fpname):  # type: ignore
        # noinspection PyProtectedMember
        super()._read(fp, fpname)  # type: ignore
        # cast section proxies to AntaresSectionProxy
        proxies = self._proxies
        for name, proxy in self._sections.items():
            if not isinstance(proxy, AntaresSectionProxy):
                proxies[name] = AntaresSectionProxy(self, name)
