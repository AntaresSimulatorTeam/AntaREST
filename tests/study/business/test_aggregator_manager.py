import zipfile
from pathlib import Path

import pytest

from antarest.core.exceptions import FileTooLargeError
from antarest.study.business.aggregator_management import AggregatorManager, MCAllAreasQueryFile
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency


@pytest.fixture(name="set_up_studies")
def studies_to_import_fixture(tmp_path: Path) -> Path:
    # Prepare the directories used by the repos
    assets_dir = Path(__file__).parent.joinpath("areas/assets/aggregator_manager")

    # Extract the sample study
    study_path = assets_dir.joinpath("viz_2.zip")
    with zipfile.ZipFile(study_path) as zip_output:
        zip_output.extractall(path=tmp_path)

    return tmp_path.joinpath("viz_2")


@pytest.mark.unit_test
def test_storage_different_max_size_value(tmp_path: Path, set_up_studies: Path):
    """
    SetUp: This test unzip the viz_2 study that contains a great number of mc values located
    in the example directory.
    Initialize one aggregator manager with a high number of output data tolerance
    and one with a low number of output data tolerance.

    Test: The call on aggregate_output_data of the first aggregator management should pass
    and the second should fail.
    """
    output_id = set_up_studies.joinpath("20230912-1354eco").name

    # aggregation_results_max_size equals to 400Mo
    aggregator_manager_high_bound = AggregatorManager(
        study_path=set_up_studies,
        output_id=output_id,
        query_file=MCAllAreasQueryFile.VALUES,
        frequency=MatrixFrequency.HOURLY,
        ids_to_consider=[],
        columns_names=[],
        aggregation_results_max_size=400,
    )

    # aggregation_results_max_size equals to 200Mo
    aggregator_manager_low_bound = AggregatorManager(
        study_path=set_up_studies,
        output_id=output_id,
        query_file=MCAllAreasQueryFile.VALUES,
        frequency=MatrixFrequency.HOURLY,
        ids_to_consider=[],
        columns_names=[],
        aggregation_results_max_size=200,
    )

    # must pass
    res = aggregator_manager_high_bound.aggregate_output_data()
    assert res.empty is False

    # must fail
    with pytest.raises(FileTooLargeError):
        aggregator_manager_low_bound.aggregate_output_data()
