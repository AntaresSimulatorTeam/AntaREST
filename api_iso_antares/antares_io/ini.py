import configparser
from pathlib import Path
from typing import Optional, Union

from api_iso_antares.types import JSON, ELEMENT


def parse_bool(value: str) -> Optional[bool]:
    return bool(value == "true") if value in ["true", "false"] else None


def parse_int(value: str) -> Optional[int]:
    try:
        return int(value)
    except ValueError:
        return None


def parse_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except ValueError:
        return None


def parse_value(value: str) -> ELEMENT:
    parsed: Union[str, int, float, bool, None] = parse_bool(value)
    parsed = parsed if parsed is not None else parse_int(value)
    parsed = parsed if parsed is not None else parse_float(value)
    return parsed if parsed is not None else value


def parse_json(json: configparser.SectionProxy) -> JSON:
    return {key: parse_value(value) for key, value in json.items()}


def read_ini(path: Path) -> JSON:
    config = configparser.ConfigParser()
    config.read(path)

    return {key: parse_json(config[key]) for key in config if key != "DEFAULT"}
