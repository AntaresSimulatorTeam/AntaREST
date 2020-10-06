import json

import pytest

from api_iso_antares.antares_io.server import application


@pytest.mark.integration_test
def test_request():

    app = application.test_client()
    res = app.get("/api/simulations/settings/generaldata.ini/general/nbyears")
    assert json.loads(res.data) == 2
