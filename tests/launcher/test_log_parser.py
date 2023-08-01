import pytest

from antarest.launcher.adapters.log_parser import LaunchProgressDTO
from tests.storage.integration.data import simulation_log


@pytest.mark.parametrize(
    "launch_progress_dto,line,expected_progression,expected_output",
    [
        (
            LaunchProgressDTO(total_mc_years=100),
            "[infos] MC-Years : [1 .. 11], total: 11",
            0,
            True,
        ),
        (
            LaunchProgressDTO(total_mc_years=10),
            "this is a test",
            0,
            False,
        ),
        (
            LaunchProgressDTO(total_mc_years=100),
            "[solver][infos] parallel batch size : 10",
            0,
            False,
        ),
        (
            LaunchProgressDTO(total_mc_years=10),
            "[solver][infos] Exporting the annual results",
            9.8,
            True,
        ),
        (
            LaunchProgressDTO(total_mc_years=10),
            "[solver][infos] Exporting the survey results",
            99,
            True,
        ),
    ],
)
def test_update_progress(
    launch_progress_dto: LaunchProgressDTO,
    line: str,
    expected_progression: float,
    expected_output: bool,
):
    output = launch_progress_dto.update_progress(line)
    assert launch_progress_dto.progress == expected_progression
    assert output == expected_output


def test_update_progress_with_real_log():
    real_log = simulation_log.simulation_log.split("\n")
    dto = LaunchProgressDTO()
    for line in real_log:
        if "Exporting the annual results" in line:
            pre_update_progress = dto.progress
            dto.update_progress(line)
            assert (
                dto.progress == pre_update_progress + 98 / dto.total_mc_years
            )
            continue
        elif "Exporting the survey results" in line:
            pre_update_progress = dto.progress
            assert pre_update_progress < 99
            dto.update_progress(line)
            assert dto.progress == 99
            continue
        elif "Quitting the solver gracefully" in line:
            assert dto.progress == 99
            dto.update_progress(line)
            assert dto.progress == 100
            continue
        dto.update_progress(line)
    assert dto.total_mc_years == 2
