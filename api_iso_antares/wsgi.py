import os
from pathlib import Path

from api_iso_antares.main import (
    get_flask_application,
)

jsm_path = Path(os.getenv("API_ANTARES_JSM_PATH"))
studies_path = Path(os.getenv("API_ANTARES_STUDIES_PATH"))

app = get_flask_application(jsm_path, studies_path)

app.config["DEBUG"] = False
