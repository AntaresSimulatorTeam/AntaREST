# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import io
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from starlette.testclient import TestClient

from antarest.study.storage.df_download import TableExportFormat
from tests.integration.raw_studies_blueprint.assets import ASSETS_DIR

# define the requests parameters for the `economy/mc-ind` outputs aggregation
AREAS_REQUESTS__IND = [
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": "values",
            "frequency": "hourly",
            "mc_years": "",
            "areas_ids": "",
            "columns_names": "",
        },
        "test-01.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": "details",
            "frequency": "hourly",
            "mc_years": "1",
            "areas_ids": "de,fr,it",
            "columns_names": "",
        },
        "test-02.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": "values",
            "frequency": "weekly",
            "mc_years": "1,2",
            "areas_ids": "",
            "columns_names": "OP. COST,MRG. PRICE",
        },
        "test-03.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": "values",
            "frequency": "hourly",
            "mc_years": "2",
            "areas_ids": "es,fr,de",
            "columns_names": "",
        },
        "test-04.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": "values",
            "frequency": "annual",
            "mc_years": "",
            "areas_ids": "",
            "columns_names": "",
        },
        "test-05.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": "values",
            "frequency": "hourly",
            "columns_names": "COSt,NODu",
        },
        "test-06.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": "details",
            "frequency": "hourly",
            "columns_names": "COSt,NODu",
        },
        "test-07.result.tsv",
    ),
]

LINKS_REQUESTS__IND = [
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": "values",
            "frequency": "hourly",
            "mc_years": "",
            "columns_names": "",
        },
        "test-01.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": "values",
            "frequency": "hourly",
            "mc_years": "1",
            "columns_names": "",
        },
        "test-02.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": "values",
            "frequency": "hourly",
            "mc_years": "1,2",
            "columns_names": "UCAP LIn.,FLOw qUAD.",
        },
        "test-03.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": "values",
            "frequency": "hourly",
            "mc_years": "1",
            "links_ids": "de - fr",
        },
        "test-04.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": "values",
            "frequency": "hourly",
            "columns_names": "MArG. COsT,CONG. PRoB +",
        },
        "test-05.result.tsv",
    ),
]

SAME_REQUEST_DIFFERENT_FORMATS__IND = [
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": "values",
            "frequency": "hourly",
            "format": "csv",
        },
        "test-01.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": "values",
            "frequency": "hourly",
            "format": "tsv",
        },
        "test-01.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": "values",
            "frequency": "hourly",
            "format": "xlsx",
        },
        "test-01.result.tsv",
    ),
]


INCOHERENT_REQUESTS_BODIES__IND = [
    {
        "output_id": "20201014-1425eco-goodbye",
        "query_file": "values",
        "frequency": "hourly",
        "mc_years": "123456789",
    },
    {
        "output_id": "20201014-1425eco-goodbye",
        "query_file": "values",
        "frequency": "hourly",
        "columns_names": "fake_col",
    },
    {
        "output_id": "20201014-1425eco-goodbye",
        "query_file": "values",
        "frequency": "hourly",
        "links_ids": "fake_id",
    },
]

WRONGLY_TYPED_REQUESTS__IND = [
    {
        "output_id": "20201014-1425eco-goodbye",
        "query_file": "fake_query_file",
        "frequency": "hourly",
    },
    {
        "output_id": "20201014-1425eco-goodbye",
        "query_file": "values",
        "frequency": "fake_frequency",
    },
    {
        "output_id": "20201014-1425eco-goodbye",
        "query_file": "values",
        "frequency": "hourly",
        "format": "fake_format",
    },
]

# define the requests parameters for the `economy/mc-all` outputs aggregation
AREAS_REQUESTS__ALL = [
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": "values",
            "frequency": "daily",
            "areas_ids": "",
            "columns_names": "",
        },
        "test-01-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": "details",
            "frequency": "monthly",
            "areas_ids": "de,fr,it",
            "columns_names": "",
        },
        "test-02-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": "values",
            "frequency": "daily",
            "areas_ids": "",
            "columns_names": "OP. CoST,MRG. PrICE",
        },
        "test-03-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": "values",
            "frequency": "daily",
            "areas_ids": "es,fr,de",
            "columns_names": "",
        },
        "test-04-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": "values",
            "frequency": "monthly",
            "areas_ids": "",
            "columns_names": "",
        },
        "test-05-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": "id",
            "frequency": "daily",
            "areas_ids": "",
            "columns_names": "",
        },
        "test-06-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": "values",
            "frequency": "daily",
            "columns_names": "COsT,NoDU",
        },
        "test-07-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": "details",
            "frequency": "monthly",
            "columns_names": "COsT,NoDU",
        },
        "test-08-all.result.tsv",
    ),
]

LINKS_REQUESTS__ALL = [
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": "values",
            "frequency": "daily",
            "columns_names": "",
        },
        "test-01-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": "values",
            "frequency": "monthly",
            "columns_names": "",
        },
        "test-02-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": "values",
            "frequency": "daily",
            "columns_names": "",
        },
        "test-03-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": "values",
            "frequency": "monthly",
            "links_ids": "de - fr",
        },
        "test-04-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": "id",
            "frequency": "daily",
            "links_ids": "",
        },
        "test-05-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": "values",
            "frequency": "daily",
            "columns_names": "MARG. COsT,CONG. ProB +",
        },
        "test-06-all.result.tsv",
    ),
]

SAME_REQUEST_DIFFERENT_FORMATS__ALL = [
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": "values",
            "frequency": "daily",
            "format": "csv",
        },
        "test-01-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": "values",
            "frequency": "daily",
            "format": "tsv",
        },
        "test-01-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": "values",
            "frequency": "daily",
            "format": "xlsx",
        },
        "test-01-all.result.tsv",
    ),
]


INCOHERENT_REQUESTS_BODIES__ALL = [
    {
        "output_id": "20201014-1427eco",
        "query_file": "values",
        "frequency": "daily",
    },
    {
        "output_id": "20201014-1427eco",
        "query_file": "values",
        "frequency": "daily",
        "columns_names": "fake_col",
    },
    {
        "output_id": "20201014-1427eco",
        "query_file": "values",
        "frequency": "monthly",
        "links_ids": "fake_id",
    },
]

WRONGLY_TYPED_REQUESTS__ALL = [
    {
        "output_id": "20201014-1427eco",
        "query_file": "fake_query_file",
        "frequency": "monthly",
    },
    {
        "output_id": "20201014-1427eco",
        "query_file": "values",
        "frequency": "fake_frequency",
    },
    {
        "output_id": "20201014-1427eco",
        "query_file": "values",
        "frequency": "daily",
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
            df = pd.read_csv(content, sep=",")
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
            df = pd.read_csv(content, sep=",")
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
                df = pd.read_csv(content, sep=",")
            elif export_format == TableExportFormat.TSV.value:
                df = pd.read_csv(content, sep="\t")
            else:
                df = pd.read_excel(content)  # type: ignore
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

    def test_aggregation_errors(
        self, client: TestClient, user_access_token: str, internal_study_id: str, tmp_path: Path
    ):
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Asserts that requests with incoherent bodies don't crash but send empty dataframes
        for params in INCOHERENT_REQUESTS_BODIES__IND:
            output_id = params.pop("output_id")
            res = client.get(f"/v1/studies/{internal_study_id}/links/aggregate/mc-ind/{output_id}", params=params)
            assert res.status_code == 200, res.json()
            assert res.content.strip() == b""

        # Asserts that wrongly typed requests send an HTTP 422 Exception
        for params in WRONGLY_TYPED_REQUESTS__IND:
            output_id = params.pop("output_id")
            res = client.get(f"/v1/studies/{internal_study_id}/links/aggregate/mc-ind/{output_id}", params=params)
            assert res.status_code == 422
            assert res.json()["exception"] == "RequestValidationError"

        # Asserts that requests with wrong output send an HTTP 422 Exception
        # for areas
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/aggregate/mc-ind/unknown_id",
            params={
                "query_file": "values",
                "frequency": "hourly",
            },
        )
        assert res.status_code == 404, res.json()
        assert res.json()["exception"] == "OutputNotFound"
        assert "unknown_id" in res.json()["description"], "The output_id should be in the message"

        # for links
        res = client.get(
            f"/v1/studies/{internal_study_id}/links/aggregate/mc-ind/unknown_id",
            params={
                "query_file": "values",
                "frequency": "hourly",
            },
        )
        assert res.status_code == 404, res.json()
        assert res.json()["exception"] == "OutputNotFound"
        assert "unknown_id" in res.json()["description"], "The output_id should be in the message"

        # Asserts that requests with non-existing folders send an HTTP 404 Exception
        # the mc-ind folder
        mc_ind_folder = tmp_path.joinpath("ext_workspace/STA-mini/output/20201014-1425eco-goodbye/economy/mc-ind")
        # delete the folder
        shutil.rmtree(mc_ind_folder)
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/aggregate/mc-ind/20201014-1425eco-goodbye",
            params={"query_file": "values", "frequency": "hourly"},
        )
        assert res.status_code == 404, res.json()
        assert "economy/mc-ind" in res.json()["description"]
        assert res.json()["exception"] == "OutputSubFolderNotFound"

    def test_empty_columns(self, client: TestClient, user_access_token: str, internal_study_id: str):
        """
        Asserts that requests get an empty dataframe when columns are not existing
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # test for areas
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/aggregate/mc-ind/20201014-1425eco-goodbye",
            params={
                "query_file": "details",
                "frequency": "hourly",
                "columns_names": "fake_col",
            },
        )
        assert res.status_code == 200, res.json()
        assert res.content.strip() == b""

        # test for links
        res = client.get(
            f"/v1/studies/{internal_study_id}/links/aggregate/mc-ind/20201014-1425eco-goodbye",
            params={
                "query_file": "values",
                "frequency": "hourly",
                "columns_names": "fake_col",
            },
        )
        assert res.status_code == 200, res.json()
        assert res.content.strip() == b""


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
            df = pd.read_csv(content, sep=",")
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
            df = pd.read_csv(content, sep=",")
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
                df = pd.read_csv(content, sep=",")
            elif export_format == TableExportFormat.TSV.value:
                df = pd.read_csv(content, sep="\t")
            else:
                df = pd.read_excel(content)  # type: ignore
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

    def test_aggregation_errors(
        self, client: TestClient, user_access_token: str, internal_study_id: str, tmp_path: Path
    ):
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Asserts that requests with incoherent bodies don't crash but send empty dataframes
        for params in INCOHERENT_REQUESTS_BODIES__ALL:
            output_id = params.pop("output_id")
            res = client.get(f"/v1/studies/{internal_study_id}/links/aggregate/mc-all/{output_id}", params=params)
            assert res.status_code == 200, res.json()
            assert res.content.strip() == b""

        # Asserts that wrongly typed requests send an HTTP 422 Exception
        for params in WRONGLY_TYPED_REQUESTS__ALL:
            output_id = params.pop("output_id")
            res = client.get(f"/v1/studies/{internal_study_id}/links/aggregate/mc-all/{output_id}", params=params)
            assert res.status_code == 422
            assert res.json()["exception"] == "RequestValidationError"

        # Asserts that requests with wrong output send an HTTP 422 Exception
        # for areas
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/aggregate/mc-all/unknown_id",
            params={
                "query_file": "values",
                "frequency": "hourly",
            },
        )
        assert res.status_code == 404, res.json()
        assert res.json()["exception"] == "OutputNotFound"
        assert "unknown_id" in res.json()["description"], "The output_id should be in the message"

        # for links
        res = client.get(
            f"/v1/studies/{internal_study_id}/links/aggregate/mc-all/unknown_id",
            params={
                "query_file": "values",
                "frequency": "hourly",
            },
        )
        assert res.status_code == 404, res.json()
        assert res.json()["exception"] == "OutputNotFound"
        assert "unknown_id" in res.json()["description"], "The output_id should be in the message"

        # Asserts that an error 404 is raised when the `economy/mc-all` folder does not exist
        mc_all_path = tmp_path.joinpath("ext_workspace/STA-mini/output/20241807-1540eco-extra-outputs/economy/mc-all")
        # delete the folder
        shutil.rmtree(mc_all_path)
        res = client.get(
            f"/v1/studies/{internal_study_id}/links/aggregate/mc-all/20241807-1540eco-extra-outputs",
            params={"query_file": "values", "frequency": "daily"},
        )
        assert res.status_code == 404, res.json()
        assert "economy/mc-all" in res.json()["description"]
        assert res.json()["exception"] == "OutputSubFolderNotFound"

    def test_empty_columns(self, client: TestClient, user_access_token: str, internal_study_id: str):
        """
        Asserts that requests get an empty dataframe when columns are not existing
        """

        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # test for areas
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/aggregate/mc-all/20201014-1427eco",
            params={
                "query_file": "details",
                "frequency": "monthly",
                "columns_names": "fake_col",
            },
        )
        assert res.status_code == 200, res.json()
        assert res.content.strip() == b""

        # test for links
        res = client.get(
            f"/v1/studies/{internal_study_id}/links/aggregate/mc-all/20241807-1540eco-extra-outputs",
            params={
                "query_file": "values",
                "frequency": "daily",
                "columns_names": "fake_col",
            },
        )
        assert res.status_code == 200, res.json()
        assert res.content.strip() == b""
