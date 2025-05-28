# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
import uuid
import zipfile
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import pytest
from starlette.testclient import TestClient

from antarest.core.serde.matrix_export import TableExportFormat
from tests.integration.assets import ASSETS_DIR as INTEGRATION_ASSETS_DIR
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


def get_file_and_task_ids(data: dict) -> Tuple[str, str]:
    file_data_id, task_id = data["download_id"], data["task_id"]
    return file_data_id, task_id


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

            download_id, task_id = get_file_and_task_ids(res.json())

            res = client.get(
                f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
            )
            assert res.status_code == 200, res.json()

            res = client.get(f"v1/downloads/{download_id}")
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

            download_id, task_id = get_file_and_task_ids(res.json())

            res = client.get(
                f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
            )
            assert res.status_code == 200, res.json()

            res = client.get(f"v1/downloads/{download_id}")
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

            download_id, task_id = get_file_and_task_ids(res.json())
            res = client.get(
                f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
            )
            assert res.status_code == 200, res.json()

            res = client.get(f"v1/downloads/{download_id}")
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
            print(f"Testing format {export_format}")
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

            download_id, task_id = get_file_and_task_ids(res.json())
            res = client.get(
                f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
            )
            assert res.status_code == 200, res.json()

            res = client.get(f"v1/downloads/{download_id}")
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
        assert res.status_code == 200, res.json()

        download_id, task_id = get_file_and_task_ids(res.json())
        res = client.get(
            f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
        )
        assert res.status_code == 422, res.json()
        assert "unknown_id" in res.json()["description"], "The output_id should be in the message"

        # for links
        res = client.get(
            f"/v1/studies/{internal_study_id}/links/aggregate/mc-ind/unknown_id",
            params={
                "query_file": "values",
                "frequency": "hourly",
            },
        )

        download_id, task_id = get_file_and_task_ids(res.json())

        res = client.get(
            f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
        )
        assert res.status_code == 422, res.json()
        assert "unknown_id" in res.json()["description"], "The output_id should be in the message"

        # Asserts that requests with non-existing folders send an HTTP 422 Exception
        # the mc-ind folder
        mc_ind_folder = tmp_path.joinpath("ext_workspace/STA-mini/output/20201014-1425eco-goodbye/economy/mc-ind")
        # delete the folder
        shutil.rmtree(mc_ind_folder)
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/aggregate/mc-ind/20201014-1425eco-goodbye",
            params={"query_file": "values", "frequency": "hourly"},
        )
        assert res.status_code == 200, res.json()

        file_data_id, task_id = get_file_and_task_ids(res.json())

        res = client.get(
            f"v1/downloads/{file_data_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
        )
        assert res.status_code == 422, res.json()
        assert "economy/mc-ind" in res.json()["description"]

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
        download_id, task_id = get_file_and_task_ids(res.json())

        res = client.get(
            f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
        )
        assert res.status_code == 200, res.json()

        res = client.get(f"v1/downloads/{download_id}")
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
        download_id, task_id = get_file_and_task_ids(res.json())

        res = client.get(
            f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
        )
        assert res.status_code == 200, res.json()

        res = client.get(f"v1/downloads/{download_id}")
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
            download_id, task_id = get_file_and_task_ids(res.json())

            res = client.get(
                f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
            )
            assert res.status_code == 200, res.json()

            res = client.get(f"v1/downloads/{download_id}")
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
            download_id, task_id = get_file_and_task_ids(res.json())

            res = client.get(
                f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
            )
            assert res.status_code == 200, res.json()

            res = client.get(f"v1/downloads/{download_id}")
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
            download_id, task_id = get_file_and_task_ids(res.json())

            res = client.get(
                f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
            )
            assert res.status_code == 200, res.json()

            res = client.get(f"v1/downloads/{download_id}")
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

    def test_with_variant(self, client: TestClient, user_access_token: str, tmp_path: Path) -> None:
        """
        Imports the STA-mini study and create a variant from it. Then imports the parent output inside it
        Then asserts the aggregation endpoint works the same for parent and variant
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Imports STA-mini
        sta_mini_zip_path = INTEGRATION_ASSETS_DIR.joinpath("STA-mini.zip")
        res = client.post("/v1/studies/_import", files={"study": io.BytesIO(sta_mini_zip_path.read_bytes())})
        study_id = res.json()
        # Create a variant from it
        variant_id = client.post(f"/v1/studies/{study_id}/variants?name=Variant_Study").json()
        res = client.get(f"/v1/studies/{variant_id}/comments")  # used to generate the study
        res.raise_for_status()

        # Build the zip output of STA-mini to import inside the variant
        raw_output_id = "20241807-1540eco-extra-outputs"
        with zipfile.ZipFile(sta_mini_zip_path) as zip_output:
            zip_output.extractall(path=tmp_path)
        output_path = tmp_path.joinpath(f"STA-mini/output/{raw_output_id}")

        sta_mini_output_zip_path = Path(
            shutil.make_archive(base_name=str(output_path), format="zip", root_dir=output_path)
        )
        output_data = io.BytesIO(sta_mini_output_zip_path.read_bytes())

        # Import the STA-mini output inside the variant
        res = client.post(f"/v1/studies/{variant_id}/output", files={"output": output_data})
        assert res.status_code == 202, res.json()
        variant_output_id = res.json()

        params = {"query_file": "values", "frequency": "daily", "format": "csv"}
        resource_file = ASSETS_DIR.joinpath("aggregate_links_raw_data/test-01-all.result.tsv")
        expected_df = pd.read_csv(resource_file, sep="\t", header=0)
        expected_df = expected_df.replace({np.nan: None})

        for study_id, output_id in [(study_id, raw_output_id), (variant_id, variant_output_id)]:
            res = client.get(f"/v1/studies/{study_id}/links/aggregate/mc-all/{output_id}", params=params)
            assert res.status_code == 200, res.json()
            download_id, task_id = get_file_and_task_ids(res.json())

            res = client.get(
                f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
            )

            assert res.status_code == 200, res.json()

            res = client.get(f"v1/downloads/{download_id}")
            assert res.status_code == 200, res.json()

            content = io.BytesIO(res.content)
            df = pd.read_csv(content, sep=",")
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
            download_id, task_id = get_file_and_task_ids(res.json())

            res = client.get(
                f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
            )
            assert res.status_code == 200, res.json()

            res = client.get(f"v1/downloads/{download_id}")
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
        download_id, task_id = get_file_and_task_ids(res.json())

        res = client.get(
            f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
        )
        assert res.status_code == 422, res.json()
        assert "Output 'unknown_id' not found" in res.json()["description"], "The output_id should be in the message"

        # for links
        res = client.get(
            f"/v1/studies/{internal_study_id}/links/aggregate/mc-all/unknown_id",
            params={
                "query_file": "values",
                "frequency": "hourly",
            },
        )
        download_id, task_id = get_file_and_task_ids(res.json())

        res = client.get(
            f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
        )
        assert res.status_code == 422, res.json()
        assert "Output 'unknown_id' not found" in res.json()["description"], (
            "The output_id that wasn't found should be in the message"
        )

        # Asserts that a 422 error is raised when the `economy/mc-all` folder does not exist
        mc_all_path = tmp_path.joinpath("ext_workspace/STA-mini/output/20241807-1540eco-extra-outputs/economy/mc-all")
        # delete the folder
        shutil.rmtree(mc_all_path)
        res = client.get(
            f"/v1/studies/{internal_study_id}/links/aggregate/mc-all/20241807-1540eco-extra-outputs",
            params={"query_file": "values", "frequency": "daily"},
        )
        download_id, task_id = get_file_and_task_ids(res.json())

        res = client.get(
            f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
        )
        assert res.status_code == 422, res.json()
        assert "economy/mc-all" in res.json()["description"]

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
        download_id, task_id = get_file_and_task_ids(res.json())

        res = client.get(
            f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
        )
        assert res.status_code == 200, res.json()

        res = client.get(f"v1/downloads/{download_id}")
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
        download_id, task_id = get_file_and_task_ids(res.json())

        res = client.get(
            f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
        )
        assert res.status_code == 200, res.json()

        res = client.get(f"v1/downloads/{download_id}")
        assert res.status_code == 200, res.json()
        assert res.content.strip() == b""


@pytest.mark.integration_test
class TestRawDataAggregationColumnsFormatting:
    def test_columns_formatting(
        self, client: TestClient, user_access_token: str, internal_study_id: str, tmp_path: Path
    ):
        """
        Check returned columns names are post-processed
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Prepare output
        output_id = "20201014-1422eco-hello"
        output_path = (
            tmp_path / "ext_workspace" / "STA-mini" / "output" / output_id / "economy" / "mc-all" / "areas" / "de"
        )
        matrix_path = ASSETS_DIR / "aggregate_areas_raw_data" / "details-STstorage-annual.txt"
        shutil.copy(matrix_path, output_path)

        # asserts STS column names are post-processed by the back-end
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/aggregate/mc-all/{output_id}",
            params={
                "query_file": "details-STstorage",
                "frequency": "annual",
            },
        )
        download_id, task_id = get_file_and_task_ids(res.json())

        res = client.get(
            f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
        )
        assert res.status_code == 200, res.json()

        res = client.get(f"v1/downloads/{download_id}")
        assert res.status_code == 200
        content = io.BytesIO(res.content)
        actual_df = pd.read_csv(content, sep=",")
        expected_df_path = ASSETS_DIR / "aggregate_areas_raw_data" / "expected_result_sts.csv"
        expected_df = pd.read_csv(expected_df_path, sep=",")
        assert actual_df.equals(expected_df)


@pytest.mark.integration
class TestDataAggregationCreationOperations:
    def test_get_aggregated_output_task_result(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ) -> None:
        """
        Test all return values when requesting the results of aggregation operations

        - test the result of an aggregation operation with a bad task_id must return a 404 code
        - test the result of an aggregation operation with a bad output_id must return a 422 code
        - try to request the results of an aggregation operation
            while the task is not completed yet and must return a 422 code
        - request the results of a correct aggregation operation: Success, 200
        """
        fake_task_id = uuid.uuid4()
        fake_file_data_id = uuid.uuid4()
        output_id = "20201014-1422eco-hello"
        params = {
            "query_file": "values",
            "frequency": "hourly",
        }
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # try to retrieve task results with a bad task_id
        # must fail with a 404 code
        res = client.get(
            f"v1/downloads/{fake_file_data_id}/metadata",
            params={"task_id": fake_task_id, "wait_for_availability": True},
        )
        assert res.status_code == 404, "failed to retrieve task {fake_task_id} in db" == res.json()["description"]

        # create a bad aggregated output task and get its id
        res = client.get(f"v1/studies/{internal_study_id}/outputs/fake_output_id/aggregate/areas/mc-ind", params=params)
        assert res.json(), res.status_code == 200

        download_id, failed_task_id = get_file_and_task_ids(res.json())

        # get error from task results
        # must return a 422 code
        res = client.get(
            f"v1/downloads/{download_id}/metadata", params={"task_id": failed_task_id, "wait_for_availability": True}
        )
        assert res.status_code == 422, "Output 'fake_output_id not found'" in res.json()["description"]

        # create a correct aggregated output task and get its id
        res = client.get(f"v1/studies/{internal_study_id}/outputs/{output_id}/aggregate/areas/mc-ind", params=params)
        assert res.status_code == 200
        download_id, task_id = get_file_and_task_ids(res.json())

        # get aggregated output too early
        # must pass with a 417 code
        res = client.get(
            f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": False}
        )
        assert res.status_code == 200, res.json()

        res = client.get(f"v1/downloads/{download_id}")
        assert res.json()["exception"] == "FileDownloadNotReady"
        assert "Requested file is not ready for download." in res.json()["description"]

        # wait for the task to be completed
        res = client.get(
            f"v1/downloads/{download_id}/metadata", params={"task_id": task_id, "wait_for_availability": True}
        )
        assert res.status_code == 200, res.json()

        res = client.get(f"v1/downloads/{download_id}")

        # get successful results
        assert res.status_code == 200, res.content
