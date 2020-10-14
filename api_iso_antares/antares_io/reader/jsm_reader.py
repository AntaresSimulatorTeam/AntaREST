import json
from pathlib import Path
from typing import Any, cast, Dict

import jsonref

from api_iso_antares.custom_types import JSON


class JsmReader:
    @staticmethod
    def read(path: Path) -> JSON:
        data = jsonref.load_uri(f"file:{path}")
        return cast(JSON, data)
