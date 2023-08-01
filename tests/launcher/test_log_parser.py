import pytest

from antarest.launcher.adapters.log_parser import LaunchProgressDTO
from tests.storage.integration.data.simulation_log import SIMULATION_LOG


@pytest.mark.parametrize(
    "launch_progress_dto, line, expected_progress, expected_result",
    [
        (
            LaunchProgressDTO(total_mc_years=100),
            "[infos] Loading the list of areas...",
            1.0,
            True,
        ),
        (
            LaunchProgressDTO(total_mc_years=100),
            "[infos] MC-Years : [1 .. 11], total: 11",
            2.0,
            True,
        ),
        (
            LaunchProgressDTO(total_mc_years=10),
            "this is a test",
            0.0,
            False,
        ),
        (
            LaunchProgressDTO(total_mc_years=100),
            "[solver][infos] parallel batch size : 10",
            0.0,
            False,
        ),
        (
            LaunchProgressDTO(total_mc_years=10),
            "[solver][infos] Exporting the annual results",
            9.6,
            True,
        ),
        (
            LaunchProgressDTO(total_mc_years=10),
            "[solver][infos] Exporting the survey results",
            99.0,
            True,
        ),
        (
            LaunchProgressDTO(total_mc_years=10),
            "[infos] [UI] Quitting the solver gracefully",
            100.0,
            True,
        ),
    ],
)
def test_parse_log_lines(
    launch_progress_dto: LaunchProgressDTO,
    line: str,
    expected_progress: float,
    expected_result: bool,
):
    output = launch_progress_dto.parse_log_lines([line])
    assert launch_progress_dto.progress == expected_progress
    assert output == expected_result


class MyLaunchProgressDTO(LaunchProgressDTO):
    update_history = []

    def _update_progress(self, line: str) -> bool:
        update = super()._update_progress(line)
        if update:
            self.update_history.append((line, self.progress))
        return update


def test_parse_log_lines__with_real_log():
    dto = MyLaunchProgressDTO()
    updated = dto.parse_log_lines(SIMULATION_LOG.splitlines())
    assert updated
    assert dto.progress == 100
    assert dto.total_mc_years == 2
    # fmt: off
    expected = [
        ("[Wed Oct 14 14:25:04 2020][solver][infos] Loading the list of areas...", 1.0),
        ("[Wed Oct 14 14:25:05 2020][solver][infos] MC-Years : [1 .. 2], total: 2", 2.0),
        ("[Wed Oct 14 14:25:05 2020][solver][infos] Exporting the annual results", 50.0),
        ("[Wed Oct 14 14:25:05 2020][solver][infos] Exporting the annual results", 98.0),
        ("[Wed Oct 14 14:25:05 2020][solver][check] Exporting the survey results...", 99.0),
        ("[Wed Oct 14 14:25:05 2020][solver][infos] [UI] Quitting the solver " "gracefully", 100.0),
    ]
    # fmt: on
    assert dto.update_history == expected
