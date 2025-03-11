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

import functools
import re
import typing as t

from antarest.core.serde import AntaresBaseModel

_SearchFunc = t.Callable[[str], t.Optional[t.Match[str]]]

_compile = functools.partial(re.compile, flags=re.IGNORECASE | re.VERBOSE)

# Search for the line indicating the loading of areas (first line of data loading).
_loading_areas = t.cast(
    _SearchFunc,
    _compile(r"Loading \s+ the \s+ list \s+ of \s+ areas").search,
)

# Search for the total number of Monté-Carlo (MC) years.
_total_mc_years = t.cast(
    _SearchFunc,
    _compile(
        r"""
        MC-Years \s* : \s*
        \[ \d+ \s* \.{2,3} \s*  \d+ ], \s* total \s* : \s*
        (?P<total_mc_years> \d+)
        """
    ).search,
)

# Search for the line indicating the export of annual results of a Monté-Carlo year.
_annual_results = t.cast(
    _SearchFunc,
    _compile(r"Exporting \s+ the \s+ annual \s+ results").search,
)

# Search for the line indicating the export of survey results.
_survey_results = t.cast(
    _SearchFunc,
    _compile(r"Exporting \s+ the \s+ survey \s+ results").search,
)

# Search for the line indicating the solver is quitting gracefully or an error
_quitting = t.cast(
    _SearchFunc,
    _compile(
        r"""
        Quitting \s+ the \s+ solver \s+ gracefully |
        \[error] |
        \[fatal]
        """
    ).search,
)


class LaunchProgressDTO(AntaresBaseModel):
    """
    Measure the progress of a study simulation.

    The progress percentage is calculated based on the number of Monté-Carlo
    years completed relative to the total number of years.

    Attributes:
        progress:
            The percentage of completion for the simulation, ranging from 0 to 100.
        total_mc_years:
            The total number of Monté-Carlo years for the simulation.
    """

    progress: float = 0
    total_mc_years: int = 1

    def _update_progress(self, line: str) -> bool:
        """Updates the progress based on the given log line."""
        if _loading_areas(line):
            self.progress = 1.0
            return True
        if mo := _total_mc_years(line):
            self.progress = 2.0
            self.total_mc_years = int(mo["total_mc_years"])
            return True
        if _annual_results(line):
            self.progress += 96 / self.total_mc_years
            return True
        if _survey_results(line):
            self.progress = 99.0
            return True
        if _quitting(line):
            self.progress = 100.0
            return True
        return False

    def parse_log_lines(self, lines: t.Iterable[str]) -> bool:
        """
        Parses a sequence of log lines and updates the progress accordingly.

        Args:
            lines (Iterable[str]): An iterable containing log lines to be parsed.

        Returns:
            bool: `True` if progress was updated at least once during the parsing,
                  `False` otherwise.
        """
        return bool(sum(self._update_progress(line) for line in lines))
