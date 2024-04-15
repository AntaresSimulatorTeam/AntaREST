import typing as t

import numpy as np
import pandas as pd
import pytest
from starlette.testclient import TestClient

from antarest.study.common.default_values import AreasQueryFile, LinksQueryFile
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from tests.integration.raw_studies_blueprint.assets import ASSETS_DIR


@pytest.mark.integration_test
class TestRawDataAggregation:
    """
    Check the aggregation of Raw Data from studies outputs
    """

    @pytest.mark.parametrize(
        "params, expected_result_filename",
        [
            (
                dict(
                    output_name="20201014-1425eco-goodbye",
                    query_file=AreasQueryFile.VALUES,
                    frequency=MatrixFrequency.HOURLY,
                    mc_years="",
                    areas_names="",
                    columns_names="",
                ),
                "test-01.result.tsv",
            ),
            (
                dict(
                    output_name="20201014-1425eco-goodbye",
                    query_file=AreasQueryFile.DETAILS,
                    frequency=MatrixFrequency.HOURLY,
                    mc_years="1",
                    areas_names="de,fr,it",
                    columns_names="",
                ),
                "test-02.result.tsv",
            ),
            (
                dict(
                    output_name="20201014-1425eco-goodbye",
                    query_file=AreasQueryFile.VALUES,
                    frequency=MatrixFrequency.WEEKLY,
                    mc_years="1,2",
                    areas_names="",
                    columns_names="OP. COST,MRG. PRICE",
                ),
                "test-03.result.tsv",
            ),
            (
                dict(
                    output_name="20201014-1425eco-goodbye",
                    query_file=AreasQueryFile.VALUES,
                    frequency=MatrixFrequency.HOURLY,
                    mc_years="2",
                    areas_names="es,fr,de",
                    columns_names="",
                ),
                "test-04.result.tsv",
            ),
        ],
    )
    def test_area_aggregation(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
        params: t.Dict[str, t.Any],
        expected_result_filename: str,
    ):
        """
        Test the aggregation of areas data
        """
        headers = {"Authorization": f"Bearer {user_access_token}"}

        res = client.get(
            f"/v1/studies/{study_id}/areas/aggregate",
            params=params,
            headers=headers,
        )
        assert res.status_code == 200
        matrix = res.json()
        df = pd.DataFrame(**matrix)
        resource_file = ASSETS_DIR.joinpath(f"aggregate_areas_raw_data/{expected_result_filename}")
        resource_file.parent.mkdir(exist_ok=True, parents=True)
        if resource_file.exists():
            # compare with previous result (non-regression test)
            expected_df = pd.read_csv(resource_file, sep="\t", header=0)
            expected_df = expected_df.replace({np.nan: None})
            # cast types of expected_df to match df
            for col in expected_df.columns:
                expected_df[col] = expected_df[col].astype(df[col].dtype)
            pd.testing.assert_frame_equal(df, expected_df)
        else:
            # create the resource
            df.to_csv(resource_file, sep="\t", index=False)
        if params["areas_names"] and matrix["columns"]:
            assert not (set(df["area"].values) - set(params["areas_names"].split(",")))
        if params["mc_years"] and matrix["columns"]:
            assert not (set(df["mcYear"].values) - set(int(i) for i in params["mc_years"].split(",")))
        if params["columns_names"] and matrix["columns"]:
            assert not (
                set(df.columns.values) - {"area", "mcYear", "time_id", "time"} - set(params["columns_names"].split(","))
            )

    @pytest.mark.parametrize(
        "params, expected_result_filename",
        [
            (
                dict(
                    output_name="20201014-1425eco-goodbye",
                    query_file=LinksQueryFile.VALUES,
                    frequency=MatrixFrequency.HOURLY,
                    mc_years="",
                    columns_names="",
                ),
                "test-01.result.tsv",
            ),
            (
                dict(
                    output_name="20201014-1425eco-goodbye",
                    query_file=LinksQueryFile.VALUES,
                    frequency=MatrixFrequency.HOURLY,
                    mc_years="1",
                    columns_names="",
                ),
                "test-02.result.tsv",
            ),
            (
                dict(
                    output_name="20201014-1425eco-goodbye",
                    query_file=LinksQueryFile.VALUES,
                    frequency=MatrixFrequency.HOURLY,
                    mc_years="1,2",
                    columns_names="UCAP LIN.,FLOW QUAD.",
                ),
                "test-03.result.tsv",
            ),
        ],
    )
    def test_links_aggregation(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
        params: t.Dict[str, t.Any],
        expected_result_filename: str,
    ):
        """
        Test the aggregation of links data
        """
        headers = {"Authorization": f"Bearer {user_access_token}"}

        res = client.get(
            f"/v1/studies/{study_id}/links/aggregate",
            params=params,
            headers=headers,
        )
        assert res.status_code == 200
        matrix = res.json()
        df = pd.DataFrame(**matrix)
        resource_file = ASSETS_DIR.joinpath(f"aggregate_links_raw_data/{expected_result_filename}")
        resource_file.parent.mkdir(exist_ok=True, parents=True)
        if resource_file.exists():
            # compare with previous result (non-regression test)
            expected_df = pd.read_csv(resource_file, sep="\t", header=0)
            expected_df = expected_df.replace({np.nan: None})
            # cast types of expected_df to match df
            for col in expected_df.columns:
                expected_df[col] = expected_df[col].astype(df[col].dtype)
            pd.testing.assert_frame_equal(df, expected_df)
        else:
            # create the resource
            df.to_csv(resource_file, sep="\t", index=False)
        if params["mc_years"] and matrix["columns"]:
            assert not (set(df["mcYear"].values) - set(int(i) for i in params["mc_years"].split(",")))
        if params["columns_names"] and matrix["columns"]:
            assert not (
                set(df.columns.values) - {"link", "mcYear", "time_id", "time"} - set(params["columns_names"].split(","))
            )
