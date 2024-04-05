import pytest
from starlette.testclient import TestClient

from antarest.study.common.default_values import AreasQueryFile
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency


@pytest.mark.integration_test
class TestRawDataAggregation:
    """
    Check the retrieval of Raw Data from studies outputs
    """

    @pytest.mark.parametrize(
        "output_name, query_file, frequency, mc_years, areas_names, columns_names",
        [
            (
                "20201014-1425eco-goodbye",
                AreasQueryFile.AREAS_VALUES,
                MatrixFrequency.ANNUAL,
                "",
                "",
                "",
            )
        ],
    )
    def test_area_aggregation(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
        output_name: str,
        query_file: AreasQueryFile,
        frequency: MatrixFrequency,
        mc_years: str,
        areas_names: str,
        columns_names: str,
    ):
        """
        Test the aggregation of areas data
        """
        headers = {"Authorization": f"Bearer {user_access_token}"}
        params = {
            "output_name": output_name,
            "query_file": query_file,
            "frequency": frequency,
            "mc_years": mc_years,
            "areas_names": areas_names,
            "columns_names": columns_names,
        }

        res = client.get(
            f"/v1/studies/{study_id}/areas/aggregate",
            params=params,
            headers=headers,
        )
        assert res.status_code == 200
