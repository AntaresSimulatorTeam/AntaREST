# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from pathlib import Path

from antarest.output.filestudy.utils import MCIndAreasQueryFile, MCIndLinksQueryFile

# Register the output metadata table before the shared database fixture creates
# all tables (the conversion itself does not otherwise need the repository).
from antarest.output.storage.v2.repository import DbOutputMetadataV2  # noqa: F401
from antarest.output.storage.v2.variables_metadata import (
    McIndFileOutput,
    ParquetAreaVariables,
    ParquetLinkVariables,
    ParquetMcAllVariableDescription,
    ParquetMcIndVariableDescription,
    ParquetRenewableClusterVariables,
    ParquetShortTermStorageVariables,
    ParquetThermalClusterVariables,
    ParquetVariablesMetadata,
    _convert_parquet_variables_metadata,
    build_mc_ind_output_mapping,
    build_mc_ind_output_mapping_2,
    get_mappings,
)


def test_convert_parquet_variables_metadata() -> None:
    metadata = ParquetVariablesMetadata(
        mc_ind_variables=[ParquetMcIndVariableDescription(name="LOAD", unit="MW", column_index=4)],
        mc_all_variables=[
            ParquetMcAllVariableDescription(name="LOAD", unit="MW", statistic_type="EXP", column_index=5)
        ],
        area_variables=[ParquetAreaVariables(area_id="area_a", variables=[0])],
        link_variables=[ParquetLinkVariables(area1_id="area_a", area2_id="area_b", variables=[0])],
        thermal_cluster_variables=[
            ParquetThermalClusterVariables(area_id="area_a", cluster_id="thermal_1", variables=[0])
        ],
        renewable_cluster_variables=[
            ParquetRenewableClusterVariables(area_id="area_a", cluster_id="wind_1", variables=[0])
        ],
        short_term_storage_variables=[
            ParquetShortTermStorageVariables(area_id="area_a", storage_id="battery_1", variables=[0])
        ],
    )

    result = _convert_parquet_variables_metadata(metadata)

    assert result.mc_ind.areas[0].area_name == "area_a"
    assert result.mc_ind.areas[0].variables[0].name == "LOAD"
    assert result.mc_ind.areas[0].variables[0].unit == "MW"
    assert result.mc_ind.areas[0].thermal_clusters[0].component_name == "thermal_1"
    assert result.mc_ind.areas[0].renewable_clusters[0].component_name == "wind_1"
    assert result.mc_ind.areas[0].short_term_storages[0].component_name == "battery_1"
    assert result.mc_ind.links[0].area_1_name == "area_a"
    assert result.mc_ind.links[0].area_2_name == "area_b"
    assert result.mc_all.areas[0].variables[0].stat == "EXP"
    assert result.mc_all.links[0].variables[0].name == "LOAD"


def test_convert_empty_parquet_variables_metadata() -> None:
    metadata = ParquetVariablesMetadata(
        mc_ind_variables=[],
        mc_all_variables=[],
        area_variables=[],
        link_variables=[],
        thermal_cluster_variables=[],
        renewable_cluster_variables=[],
        short_term_storage_variables=[],
    )

    result = _convert_parquet_variables_metadata(metadata)

    assert result.mc_ind.areas == []
    assert result.mc_ind.links == []
    assert result.mc_all.areas == []
    assert result.mc_all.links == []


def test_mc_ind_build_output_mappign() -> None:
    output_dir = Path("/home/leclercsyl/feature_tests/antares/output-agregation/output/20250127-1459eco")
    mapping = build_mc_ind_output_mapping(output_dir)
    size = len(mapping)
    assert size == 1590


def test_mc_ind_build_file_mappign() -> None:
    output_dir = Path("/home/leclercsyl/feature_tests/antares/output-agregation/output/20250127-1459eco")
    output = McIndFileOutput(output_dir)
    mapping = get_mappings(output)
    assert len(mapping.area_values_mappings) == 3
    assert len(mapping.area_details_mappings) == 2
    assert len(mapping.area_details_res_mappings) == 1
    assert len(mapping.area_details_sts_mappings) == 0
    assert len(mapping.link_values_mappings) == 47

    print(mapping.area_values_mappings)


def test_type_matching():
    toto: MCIndAreasQueryFile = MCIndAreasQueryFile.VALUES
    assert toto == "values"
    assert toto is MCIndAreasQueryFile.VALUES
    assert toto in MCIndAreasQueryFile
    assert toto in MCIndLinksQueryFile
    assert MCIndLinksQueryFile.VALUES == MCIndAreasQueryFile.VALUES
    assert MCIndLinksQueryFile.VALUES is MCIndAreasQueryFile.VALUES
    assert isinstance(toto, MCIndAreasQueryFile)
    assert isinstance(toto, MCIndLinksQueryFile)
