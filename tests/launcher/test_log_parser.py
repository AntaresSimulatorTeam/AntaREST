import pytest

from antarest.launcher.adapters.log_parser import LaunchProgressDTO, LogParser


@pytest.mark.parametrize(
    "launch_progress_dto,line,expected_progression,expected_output",
    [
        (
            LaunchProgressDTO(N_K=100, N_ANNUAL_RESULT=10),
            "[infos] MC-Years : [1 .. 11], total: 11",
            0,
            True,
        ),
        (
            LaunchProgressDTO(N_K=100, N_ANNUAL_RESULT=10),
            "this is a test",
            0,
            False,
        ),
        (
            LaunchProgressDTO(N_K=100, N_ANNUAL_RESULT=10),
            "[solver][infos] parallel batch size : 10",
            9 * 0.8,
            True,
        ),
        (
            LaunchProgressDTO(N_K=100, N_ANNUAL_RESULT=10),
            "[solver][infos] Exporting the annual results",
            0.8 * 9 * 1 / 10,
            True,
        ),
        (
            LaunchProgressDTO(N_K=100, N_ANNUAL_RESULT=10),
            "[solver][infos] Exporting the survey results",
            99 * 0.8,
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
    output = LogParser.update_progress(line, launch_progress_dto)
    assert launch_progress_dto.progress == expected_progression
    assert output == expected_output
