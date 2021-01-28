import os
from pathlib import Path


from antarest.storage_api.main import (
    get_flask_application,
)


def get_env_var(env_var_name: str) -> str:
    env_var = os.getenv(env_var_name)
    if env_var is None:
        raise EnvironmentError(f"API need the env var: {env_var_name}.")
    return env_var


env_var_studies_path = get_env_var("API_ANTARES_STUDIES_PATH")
studies_path = Path(env_var_studies_path)

app = get_flask_application(studies_path)

app.config["DEBUG"] = False
