from api_iso_antares.main import (
    get_flask_application_by_environment_variables,
)

app = get_flask_application_by_environment_variables()

app.config["DEBUG"] = False
