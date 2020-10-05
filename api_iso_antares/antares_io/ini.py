import configparser
from pathlib import Path


def read_ini(path: Path) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(path)

    return config
