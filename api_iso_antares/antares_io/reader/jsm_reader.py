from pathlib import Path
from pathlib import Path
from typing import cast

import jsonref

from api_iso_antares.custom_types import JSON


class JsmReader:
    @staticmethod
    def read(path: Path) -> JSON:
        data = jsonref.load_uri(path.resolve().as_uri())
        return cast(JSON, data)
