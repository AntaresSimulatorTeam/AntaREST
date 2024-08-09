import io

import numpy as np
import pandas as pd
import pytest
from starlette.testclient import TestClient

from antarest.study.business.aggregator_management import (
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
)
from antarest.study.storage.df_download import TableExportFormat
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from tests.integration.raw_studies_blueprint.assets import ASSETS_DIR

# define the requests parameters for the `economy/mc-ind` outputs aggregation
AREAS_REQUESTS__IND = [
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndAreasQueryFile.VALUES,
            "frequency": MatrixFrequency.HOURLY,
            "mc_years": "",
            "areas_ids": "",
            "columns_names": "",
        },
        "test-01.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndAreasQueryFile.DETAILS,
            "frequency": MatrixFrequency.HOURLY,
            "mc_years": "1",
            "areas_ids": "de,fr,it",
            "columns_names": "",
        },
        "test-02.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndAreasQueryFile.VALUES,
            "frequency": MatrixFrequency.WEEKLY,
            "mc_years": "1,2",
            "areas_ids": "",
            "columns_names": "OP. COST,MRG. PRICE",
        },
        "test-03.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndAreasQueryFile.VALUES,
            "frequency": MatrixFrequency.HOURLY,
            "mc_years": "2",
            "areas_ids": "es,fr,de",
            "columns_names": "",
        },
        "test-04.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndAreasQueryFile.VALUES,
            "frequency": MatrixFrequency.ANNUAL,
            "mc_years": "",
            "areas_ids": "",
            "columns_names": "",
        },
        "test-05.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndAreasQueryFile.VALUES,
            "frequency": MatrixFrequency.HOURLY,
            "columns_names": "COSt,NODu",
        },
        "test-06.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndAreasQueryFile.DETAILS,
            "frequency": MatrixFrequency.HOURLY,
            "columns_names": "COSt,NODu",
        },
        "test-07.result.tsv",
    ),
]

LINKS_REQUESTS__IND = [
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndLinksQueryFile.VALUES,
            "frequency": MatrixFrequency.HOURLY,
            "mc_years": "",
            "columns_names": "",
        },
        "test-01.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndLinksQueryFile.VALUES,
            "frequency": MatrixFrequency.HOURLY,
            "mc_years": "1",
            "columns_names": "",
        },
        "test-02.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndLinksQueryFile.VALUES,
            "frequency": MatrixFrequency.HOURLY,
            "mc_years": "1,2",
            "columns_names": "UCAP LIn.,FLOw qUAD.",
        },
        "test-03.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndLinksQueryFile.VALUES,
            "frequency": MatrixFrequency.HOURLY,
            "mc_years": "1",
            "links_ids": "de - fr",
        },
        "test-04.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndLinksQueryFile.VALUES,
            "frequency": MatrixFrequency.HOURLY,
            "columns_names": "MArG. COsT,CONG. PRoB +",
        },
        "test-05.result.tsv",
    ),
]

SAME_REQUEST_DIFFERENT_FORMATS__IND = [
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndLinksQueryFile.VALUES,
            "frequency": MatrixFrequency.HOURLY,
            "format": "csv",
        },
        "test-01.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndLinksQueryFile.VALUES,
            "frequency": MatrixFrequency.HOURLY,
            "format": "tsv",
        },
        "test-01.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndLinksQueryFile.VALUES,
            "frequency": MatrixFrequency.HOURLY,
            "format": "xlsx",
        },
        "test-01.result.tsv",
    ),
]


INCOHERENT_REQUESTS_BODIES__IND = [
    {
        "output_id": "20201014-1425eco-goodbye",
        "query_file": MCIndAreasQueryFile.VALUES,
        "frequency": MatrixFrequency.HOURLY,
        "mc_years": "123456789",
    },
    {
        "output_id": "20201014-1425eco-goodbye",
        "query_file": MCIndLinksQueryFile.VALUES,
        "frequency": MatrixFrequency.HOURLY,
        "columns_names": "fake_col",
    },
    {
        "output_id": "20201014-1425eco-goodbye",
        "query_file": MCIndAreasQueryFile.VALUES,
        "frequency": MatrixFrequency.HOURLY,
        "links_ids": "fake_id",
    },
]

WRONGLY_TYPED_REQUESTS__IND = [
    {
        "output_id": "20201014-1425eco-goodbye",
        "query_file": "fake_query_file",
        "frequency": MatrixFrequency.HOURLY,
    },
    {
        "output_id": "20201014-1425eco-goodbye",
        "query_file": MCIndAreasQueryFile.VALUES,
        "frequency": "fake_frequency",
    },
    {
        "output_id": "20201014-1425eco-goodbye",
        "query_file": MCIndAreasQueryFile.VALUES,
        "frequency": MatrixFrequency.HOURLY,
        "format": "fake_format",
    },
]

# define the requests parameters for the `economy/mc-all` outputs aggregation
AREAS_REQUESTS__ALL = [
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreasQueryFile.VALUES,
            "frequency": MatrixFrequency.DAILY,
            "areas_ids": "",
            "columns_names": "",
        },
        "test-01-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreasQueryFile.DETAILS,
            "frequency": MatrixFrequency.MONTHLY,
            "areas_ids": "de,fr,it",
            "columns_names": "",
        },
        "test-02-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreasQueryFile.VALUES,
            "frequency": MatrixFrequency.DAILY,
            "areas_ids": "",
            "columns_names": "OP. CoST,MRG. PrICE",
        },
        "test-03-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreasQueryFile.VALUES,
            "frequency": MatrixFrequency.DAILY,
            "areas_ids": "es,fr,de",
            "columns_names": "",
        },
        "test-04-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreasQueryFile.VALUES,
            "frequency": MatrixFrequency.MONTHLY,
            "areas_ids": "",
            "columns_names": "",
        },
        "test-05-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreasQueryFile.ID,
            "frequency": MatrixFrequency.DAILY,
            "areas_ids": "",
            "columns_names": "",
        },
        "test-06-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreasQueryFile.VALUES,
            "frequency": MatrixFrequency.DAILY,
            "columns_names": "COsT,NoDU",
        },
        "test-07-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreasQueryFile.DETAILS,
            "frequency": MatrixFrequency.MONTHLY,
            "columns_names": "COsT,NoDU",
        },
        "test-08-all.result.tsv",
    ),
]

LINKS_REQUESTS__ALL = [
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": MCAllLinksQueryFile.VALUES,
            "frequency": MatrixFrequency.DAILY,
            "columns_names": "",
        },
        "test-01-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": MCAllLinksQueryFile.VALUES,
            "frequency": MatrixFrequency.MONTHLY,
            "columns_names": "",
        },
        "test-02-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": MCAllLinksQueryFile.VALUES,
            "frequency": MatrixFrequency.DAILY,
            "columns_names": "",
        },
        "test-03-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": MCAllLinksQueryFile.VALUES,
            "frequency": MatrixFrequency.MONTHLY,
            "links_ids": "de - fr",
        },
        "test-04-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": MCAllLinksQueryFile.ID,
            "frequency": MatrixFrequency.DAILY,
            "links_ids": "",
        },
        "test-05-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": MCAllLinksQueryFile.VALUES,
            "frequency": MatrixFrequency.DAILY,
            "columns_names": "MARG. COsT,CONG. ProB +",
        },
        "test-06-all.result.tsv",
    ),
]

SAME_REQUEST_DIFFERENT_FORMATS__ALL = [
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": MCAllLinksQueryFile.VALUES,
            "frequency": MatrixFrequency.DAILY,
            "format": "csv",
        },
        "test-01-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": MCAllLinksQueryFile.VALUES,
            "frequency": MatrixFrequency.DAILY,
            "format": "tsv",
        },
        "test-01-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": MCAllLinksQueryFile.VALUES,
            "frequency": MatrixFrequency.DAILY,
            "format": "xlsx",
        },
        "test-01-all.result.tsv",
    ),
]


INCOHERENT_REQUESTS_BODIES__ALL = [
    {
        "output_id": "20201014-1427eco",
        "query_file": MCAllAreasQueryFile.VALUES,
        "frequency": MatrixFrequency.DAILY,
    },
    {
        "output_id": "20201014-1427eco",
        "query_file": MCAllLinksQueryFile.VALUES,
        "frequency": MatrixFrequency.DAILY,
        "columns_names": "fake_col",
    },
    {
        "output_id": "20201014-1427eco",
        "query_file": MCAllAreasQueryFile.VALUES,
        "frequency": MatrixFrequency.MONTHLY,
        "links_ids": "fake_id",
    },
]

WRONGLY_TYPED_REQUESTS__ALL = [
    {
        "output_id": "20201014-1427eco",
        "query_file": "fake_query_file",
        "frequency": MatrixFrequency.MONTHLY,
    },
    {
        "output_id": "20201014-1427eco",
        "query_file": MCAllAreasQueryFile.VALUES,
        "frequency": "fake_frequency",
    },
    {
        "output_id": "20201014-1427eco",
        "query_file": MCAllAreasQueryFile.VALUES,
        "frequency": MatrixFrequency.DAILY,
        "format": "fake_format",
    },
]


@pytest.mark.integration_test
class TestRawDataAggregationMCInd:
    """
    Check the aggregation of Raw Data from studies outputs
    """

    def test_area_aggregation(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ):
        """
        Test the aggregation of areas data
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        for params, expected_result_filename in AREAS_REQUESTS__IND:
            output_id = params.pop("output_id")
            res = client.get(f"/v1/studies/{internal_study_id}/areas/aggregate/mc-ind/{output_id}", params=params)
            assert res.status_code == 200, res.json()
            content = io.BytesIO(res.content)
            df = pd.read_csv(content, index_col=0, sep=",")
            resource_file = ASSETS_DIR.joinpath(f"aggregate_areas_raw_data/{expected_result_filename}")
            resource_file.parent.mkdir(exist_ok=True, parents=True)
            if not resource_file.exists():
                # create the resource to add it to non-regression tests
                df.to_csv(resource_file, sep="\t", index=False)
            expected_df = pd.read_csv(resource_file, sep="\t", header=0)
            expected_df = expected_df.replace({np.nan: None})
            # cast types of expected_df to match df
            for col in expected_df.columns:
                expected_df[col] = expected_df[col].astype(df[col].dtype)
            pd.testing.assert_frame_equal(df, expected_df)

    def test_links_aggregation(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ):
        """
        Test the aggregation of links data
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        for params, expected_result_filename in LINKS_REQUESTS__IND:
            output_id = params.pop("output_id")
            res = client.get(f"/v1/studies/{internal_study_id}/links/aggregate/mc-ind/{output_id}", params=params)
            assert res.status_code == 200, res.json()
            content = io.BytesIO(res.content)
            df = pd.read_csv(content, index_col=0, sep=",")
            resource_file = ASSETS_DIR.joinpath(f"aggregate_links_raw_data/{expected_result_filename}")
            resource_file.parent.mkdir(exist_ok=True, parents=True)
            if not resource_file.exists():
                # create the resource to add it to non-regression tests
                df.to_csv(resource_file, sep="\t", index=False)
            expected_df = pd.read_csv(resource_file, sep="\t", header=0)
            expected_df = expected_df.replace({np.nan: None})
            # cast types of expected_df to match df
            for col in expected_df.columns:
                expected_df[col] = expected_df[col].astype(df[col].dtype)
            pd.testing.assert_frame_equal(df, expected_df)

    def test_different_formats(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ):
        """
        Tests that all formats work and produce the same result
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        for params, expected_result_filename in SAME_REQUEST_DIFFERENT_FORMATS__IND:
            output_id = params.pop("output_id")
            res = client.get(f"/v1/studies/{internal_study_id}/links/aggregate/mc-ind/{output_id}", params=params)
            assert res.status_code == 200, res.json()
            content = io.BytesIO(res.content)
            export_format = params["format"]
            if export_format == TableExportFormat.CSV.value:
                df = pd.read_csv(content, index_col=0, sep=",")
            elif export_format == TableExportFormat.TSV.value:
                df = pd.read_csv(content, index_col=0, sep="\t")
            else:
                df = pd.read_excel(content, index_col=0)  # type: ignore
            resource_file = ASSETS_DIR.joinpath(f"aggregate_links_raw_data/{expected_result_filename}")
            resource_file.parent.mkdir(exist_ok=True, parents=True)
            if not resource_file.exists():
                # create the resource to add it to non-regression tests
                df.to_csv(resource_file, sep="\t", index=False)
            expected_df = pd.read_csv(resource_file, sep="\t", header=0)
            expected_df = expected_df.replace({np.nan: None})
            # cast types of expected_df to match df
            for col in expected_df.columns:
                expected_df[col] = expected_df[col].astype(df[col].dtype)
            pd.testing.assert_frame_equal(df, expected_df)

    def test_aggregation_with_incoherent_bodies(
        self, client: TestClient, user_access_token: str, internal_study_id: str
    ):
        """
        Asserts that requests with incoherent bodies don't crash but send empty dataframes
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        for params in INCOHERENT_REQUESTS_BODIES__IND:
            output_id = params.pop("output_id")
            res = client.get(f"/v1/studies/{internal_study_id}/links/aggregate/mc-ind/{output_id}", params=params)
            assert res.status_code == 200, res.json()
            content = io.BytesIO(res.content)
            df = pd.read_csv(content, index_col=0, sep=",")
            assert df.empty

    def test_wrongly_typed_request(self, client: TestClient, user_access_token: str, internal_study_id: str):
        """
        Asserts that wrongly typed requests send an HTTP 422 Exception
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        for params in WRONGLY_TYPED_REQUESTS__IND:
            output_id = params.pop("output_id")
            res = client.get(f"/v1/studies/{internal_study_id}/links/aggregate/mc-ind/{output_id}", params=params)
            assert res.status_code == 422
            assert res.json()["exception"] == "RequestValidationError"

    def test_aggregation_with_wrong_output(self, client: TestClient, user_access_token: str, internal_study_id: str):
        """
        Asserts that requests with wrong output send an HTTP 422 Exception
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # test for areas
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/aggregate/mc-ind/unknown_id",
            params={
                "query_file": MCIndAreasQueryFile.VALUES,
                "frequency": MatrixFrequency.HOURLY,
            },
        )
        assert res.status_code == 404, res.json()
        assert res.json()["exception"] == "OutputNotFound"
        assert "unknown_id" in res.json()["description"], "The output_id should be in the message"

        # test for links
        res = client.get(
            f"/v1/studies/{internal_study_id}/links/aggregate/mc-ind/unknown_id",
            params={
                "query_file": MCIndLinksQueryFile.VALUES,
                "frequency": MatrixFrequency.HOURLY,
            },
        )
        assert res.status_code == 404, res.json()
        assert res.json()["exception"] == "OutputNotFound"
        assert "unknown_id" in res.json()["description"], "The output_id should be in the message"

    def test_empty_columns(self, client: TestClient, user_access_token: str, internal_study_id: str):
        """
        Asserts that requests get an empty dataframe when columns are not existing
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # test for areas
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/aggregate/mc-ind/20201014-1425eco-goodbye",
            params={
                "query_file": MCIndAreasQueryFile.DETAILS,
                "frequency": MatrixFrequency.HOURLY,
                "columns_names": "fake_col",
            },
        )
        assert res.status_code == 200, res.json()
        df = pd.read_csv(io.BytesIO(res.content), index_col=0, sep=",")
        assert df.empty

        # test for links
        res = client.get(
            f"/v1/studies/{internal_study_id}/links/aggregate/mc-ind/20201014-1425eco-goodbye",
            params={
                "query_file": MCIndLinksQueryFile.VALUES,
                "frequency": MatrixFrequency.HOURLY,
                "columns_names": "fake_col",
            },
        )
        assert res.status_code == 200, res.json()
        df = pd.read_csv(io.BytesIO(res.content), index_col=0, sep=",")
        assert df.empty


@pytest.mark.integration_test
class TestRawDataAggregationMCAll:
    """
    Check the aggregation of Raw Data from studies outputs in `economy/mc-all`
    """

    def test_area_aggregation(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ):
        """
        Test the aggregation of areas data
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        for params, expected_result_filename in AREAS_REQUESTS__ALL:
            output_id = params.pop("output_id")
            res = client.get(f"/v1/studies/{internal_study_id}/areas/aggregate/mc-all/{output_id}", params=params)
            assert res.status_code == 200, res.json()
            content = io.BytesIO(res.content)
            df = pd.read_csv(content, index_col=0, sep=",")
            resource_file = ASSETS_DIR.joinpath(f"aggregate_areas_raw_data/{expected_result_filename}")
            resource_file.parent.mkdir(exist_ok=True, parents=True)
            if not resource_file.exists():
                # create the resource to add it to non-regression tests
                df.to_csv(resource_file, sep="\t", index=False)
            expected_df = pd.read_csv(resource_file, sep="\t", header=0)
            expected_df = expected_df.replace({np.nan: None})
            # cast types of expected_df to match df
            for col in expected_df.columns:
                expected_df[col] = expected_df[col].astype(df[col].dtype)
            pd.testing.assert_frame_equal(df, expected_df)

    def test_links_aggregation(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ):
        """
        Test the aggregation of links data
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        for params, expected_result_filename in LINKS_REQUESTS__ALL:
            output_id = params.pop("output_id")
            res = client.get(f"/v1/studies/{internal_study_id}/links/aggregate/mc-all/{output_id}", params=params)
            assert res.status_code == 200, res.json()
            content = io.BytesIO(res.content)
            df = pd.read_csv(content, index_col=0, sep=",")
            resource_file = ASSETS_DIR.joinpath(f"aggregate_links_raw_data/{expected_result_filename}")
            resource_file.parent.mkdir(exist_ok=True, parents=True)
            if not resource_file.exists():
                # create the resource to add it to non-regression tests
                df.to_csv(resource_file, sep="\t", index=False)
            expected_df = pd.read_csv(resource_file, sep="\t", header=0)
            expected_df = expected_df.replace({np.nan: None})
            # cast types of expected_df to match df
            for col in expected_df.columns:
                expected_df[col] = expected_df[col].astype(df[col].dtype)
            pd.testing.assert_frame_equal(df, expected_df)

    def test_different_formats(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ):
        """
        Tests that all formats work and produce the same result
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        for params, expected_result_filename in SAME_REQUEST_DIFFERENT_FORMATS__ALL:
            output_id = params.pop("output_id")
            res = client.get(f"/v1/studies/{internal_study_id}/links/aggregate/mc-all/{output_id}", params=params)
            assert res.status_code == 200, res.json()
            content = io.BytesIO(res.content)
            export_format = params["format"]
            if export_format == TableExportFormat.CSV.value:
                df = pd.read_csv(content, index_col=0, sep=",")
            elif export_format == TableExportFormat.TSV.value:
                df = pd.read_csv(content, index_col=0, sep="\t")
            else:
                df = pd.read_excel(content, index_col=0)  # type: ignore
            resource_file = ASSETS_DIR.joinpath(f"aggregate_links_raw_data/{expected_result_filename}")
            resource_file.parent.mkdir(exist_ok=True, parents=True)
            if not resource_file.exists():
                # create the resource to add it to non-regression tests
                df.to_csv(resource_file, sep="\t", index=False)
            expected_df = pd.read_csv(resource_file, sep="\t", header=0)
            expected_df = expected_df.replace({np.nan: None})
            # cast types of expected_df to match df
            for col in expected_df.columns:
                expected_df[col] = expected_df[col].astype(df[col].dtype)
            pd.testing.assert_frame_equal(df, expected_df)

    def test_aggregation_with_incoherent_bodies(
        self, client: TestClient, user_access_token: str, internal_study_id: str
    ):
        """
        Asserts that requests with incoherent bodies don't crash but send empty dataframes
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        for params in INCOHERENT_REQUESTS_BODIES__ALL:
            output_id = params.pop("output_id")
            res = client.get(f"/v1/studies/{internal_study_id}/links/aggregate/mc-all/{output_id}", params=params)
            assert res.status_code == 200, res.json()
            content = io.BytesIO(res.content)
            df = pd.read_csv(content, index_col=0, sep=",")
            assert df.empty

    def test_wrongly_typed_request(self, client: TestClient, user_access_token: str, internal_study_id: str):
        """
        Asserts that wrongly typed requests send an HTTP 422 Exception
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        for params in WRONGLY_TYPED_REQUESTS__ALL:
            output_id = params.pop("output_id")
            res = client.get(f"/v1/studies/{internal_study_id}/links/aggregate/mc-all/{output_id}", params=params)
            assert res.status_code == 422
            assert res.json()["exception"] == "RequestValidationError"

    def test_aggregation_with_wrong_output(self, client: TestClient, user_access_token: str, internal_study_id: str):
        """
        Asserts that requests with wrong output send an HTTP 422 Exception
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # test for areas
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/aggregate/mc-all/unknown_id",
            params={
                "query_file": MCIndAreasQueryFile.VALUES,
                "frequency": MatrixFrequency.HOURLY,
            },
        )
        assert res.status_code == 404, res.json()
        assert res.json()["exception"] == "OutputNotFound"
        assert "unknown_id" in res.json()["description"], "The output_id should be in the message"

        # test for links
        res = client.get(
            f"/v1/studies/{internal_study_id}/links/aggregate/mc-all/unknown_id",
            params={
                "query_file": MCIndLinksQueryFile.VALUES,
                "frequency": MatrixFrequency.HOURLY,
            },
        )
        assert res.status_code == 404, res.json()
        assert res.json()["exception"] == "OutputNotFound"
        assert "unknown_id" in res.json()["description"], "The output_id should be in the message"

    def test_empty_columns(self, client: TestClient, user_access_token: str, internal_study_id: str):
        """
        Asserts that requests get an empty dataframe when columns are not existing
        """

        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # test for areas
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/aggregate/mc-all/20201014-1427eco",
            params={
                "query_file": MCAllAreasQueryFile.DETAILS,
                "frequency": MatrixFrequency.MONTHLY,
                "columns_names": "fake_col",
            },
        )
        assert res.status_code == 200, res.json()
        df = pd.read_csv(io.BytesIO(res.content), index_col=0, sep=",")
        assert df.empty

        # test for links
        res = client.get(
            f"/v1/studies/{internal_study_id}/links/aggregate/mc-all/20241807-1540eco-extra-outputs",
            params={
                "query_file": MCAllLinksQueryFile.VALUES,
                "frequency": MatrixFrequency.DAILY,
                "columns_names": "fake_col",
            },
        )
        assert res.status_code == 200, res.json()
        df = pd.read_csv(io.BytesIO(res.content), index_col=0, sep=",")
        assert df.empty
