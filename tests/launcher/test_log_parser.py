import json
import sys
from typing import List, Union

import pytest

from antarest.launcher.adapters.log_parser import LaunchProgressDTO
from tests.launcher.assets import ASSETS_DIR


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
) -> None:
    output = launch_progress_dto.parse_log_lines([line])
    assert launch_progress_dto.progress == expected_progress
    assert output == expected_result


HistoryType = List[List[Union[str, float]]]


class MyLaunchProgressDTO(LaunchProgressDTO):
    history: HistoryType = []

    def _update_progress(self, line: str) -> bool:
        update = super()._update_progress(line)
        if update:
            self.history.append([line, self.progress])
        return update


@pytest.mark.parametrize(
    "filename",
    [
        "simulation.error.log",
        "simulation.error-big.log",
        "simulation.fatal.log",
        "simulation.nominal.log",
        "simulation.nominal-big.log",
    ],
)
def test_parse_log_lines__non_regression_test(filename: str) -> None:
    log_path = ASSETS_DIR / "log_parser" / filename
    lines = log_path.read_text(encoding="utf-8").splitlines()
    dto = MyLaunchProgressDTO()
    updated = dto.parse_log_lines(lines)
    assert updated
    # check history
    history_path = log_path.with_suffix(".history.json")
    if history_path.exists():
        expected = json.loads(history_path.read_text(encoding="utf-8"))
        assert dto.history == expected
    else:
        with history_path.open(mode="w", encoding="utf-8") as fd:
            fd.write(json.dumps(dto.history, ensure_ascii=False, indent=True))
        print(
            f"\nWARNING: check the result in '{history_path.relative_to(ASSETS_DIR)}'" f" and commit the file in Git",
            file=sys.stderr,
        )
