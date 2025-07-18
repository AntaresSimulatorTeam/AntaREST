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
import pathlib

import pytest
from antares.study.version import StudyVersion
from antares.study.version.create_app import CreateApp

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import GeneralData


@pytest.mark.parametrize(
    "version", ["700", "710", "720", "800", "810", "820", "830", "840", "850", "860", "870", "880", "920", "930"]
)
def test_general_data_content(tmp_path: pathlib.Path, version: StudyVersion):
    study_path = tmp_path / "test"
    app = CreateApp(study_dir=study_path, caption="Test", version=version, author="Unknown")
    app()

    config = FileStudyTreeConfig(study_path=study_path, path=study_path, study_id="test", version=version)
    general_data = GeneralData(config)
    data = general_data.types

    parsed_version = StudyVersion.parse(version)

    # ========== COMMON FIELDS TESTS FOR ALL VERSIONS ==========

    # Sections present in all versions
    assert "general" in data
    assert "input" in data
    assert "output" in data
    assert "optimization" in data
    assert "other preferences" in data
    assert "advanced parameters" in data
    assert "seeds - Mersenne Twister" in data

    # Section "general" - fields common to all versions (except version-specific ones)
    general = data["general"]
    assert "mode" in general
    assert "horizon" in general
    assert "nbyears" in general
    assert "simulation.start" in general
    assert "simulation.end" in general
    assert "january.1st" in general
    assert "first-month-in-year" in general
    assert "first.weekday" in general
    assert "leapyear" in general
    assert "year-by-year" in general
    assert "derated" in general
    assert "user-playlist" in general
    assert "active-rules-scenario" in general
    assert "generate" in general
    assert "nbtimeseriesload" in general
    assert "nbtimeserieshydro" in general
    assert "nbtimeserieswind" in general
    assert "nbtimeseriesthermal" in general
    assert "nbtimeseriessolar" in general
    assert "intra-modal" in general
    assert "inter-modal" in general
    assert "readonly" in general

    # Section "input" - common to all versions
    assert "import" in data["input"]

    # Section "output" - common to all versions
    output = data["output"]
    assert "synthesis" in output
    assert "storenewset" in output
    assert "archives" in output

    # Section "optimization" - fields common to all versions
    optimization = data["optimization"]
    assert "simplex-range" in optimization
    assert "transmission-capacities" in optimization
    assert "include-constraints" in optimization
    assert "include-hurdlecosts" in optimization
    assert "include-tc-minstablepower" in optimization
    assert "include-tc-min-ud-time" in optimization
    assert "include-dayahead" in optimization
    assert "include-strategicreserve" in optimization
    assert "include-spinningreserve" in optimization
    assert "include-primaryreserve" in optimization
    assert "include-exportmps" in optimization

    # Section "other preferences" - fields common to all versions
    other_preferences = data["other preferences"]
    assert "power-fluctuations" in other_preferences
    assert "shedding-strategy" in other_preferences
    assert "shedding-policy" in other_preferences
    assert "unit-commitment-mode" in other_preferences
    assert "number-of-cores-mode" in other_preferences
    assert "day-ahead-reserve-management" in other_preferences

    # Section "advanced parameters" - common to all versions
    advanced = data["advanced parameters"]
    assert "accuracy-on-correlation" in advanced
    assert "adequacy-block-size" in advanced

    # Section "seeds - Mersenne Twister" - common to all versions
    seeds = data["seeds - Mersenne Twister"]
    assert "seed-tsgen-wind" in seeds
    assert "seed-tsgen-load" in seeds
    assert "seed-tsgen-hydro" in seeds
    assert "seed-tsgen-thermal" in seeds
    assert "seed-tsgen-solar" in seeds
    assert "seed-tsnumbers" in seeds
    assert "seed-unsupplied-energy-costs" in seeds
    assert "seed-spilled-energy-costs" in seeds
    assert "seed-thermal-costs" in seeds
    assert "seed-hydro-costs" in seeds
    assert "seed-initial-reservoir-levels" in seeds

    # ========== VERSION-SPECIFIC CHANGES TESTS ==========

    # Version 7.0.0 - Added link-type and initial-reservoir-levels
    if parsed_version >= 700:
        assert "link-type" in optimization
        if parsed_version < 920:  # removed in 9.2.0
            assert "initial-reservoir-levels" in other_preferences

    # Version 7.1.0 - Removed filtering, added trimming fields
    if parsed_version >= 710:
        assert "filtering" not in general
        assert "thematic-trimming" in general
        assert "geographic-trimming" in general

    # Version 7.2.0 - Added hydro-pricing-mode
    if parsed_version >= 720:
        assert "hydro-pricing-mode" in other_preferences

    # Version 8.0.0 - Replaced custom-ts-numbers with custom-scenario, added new fields
    if parsed_version >= 800:
        assert "custom-ts-numbers" not in general
        assert "custom-scenario" in general
        assert "include-exportstructure" in optimization
        assert "include-unfeasible-problem-behavior" in optimization
        assert "hydro-heuristic-policy" in other_preferences

    # Version 8.1.0 - Added renewable-generation-modelling
    if parsed_version >= 810:
        assert "renewable-generation-modelling" in other_preferences

    # Version 8.3.0 - Added adequacy patch section
    if parsed_version >= 830:
        assert "adequacy patch" in data
        adequacy = data["adequacy patch"]
        assert "include-adq-patch" in adequacy
        assert "set-to-null-ntc-from-physical-out-to-physical-in-for-first-step" in adequacy
        if parsed_version < 920:  # removed in 9.2.0
            assert "set-to-null-ntc-between-physical-out-for-first-step" in adequacy
        if parsed_version == 830:  # only in 8.3.0
            assert "include-split-exported-mps" in optimization

    # Version 8.4.0 - Removed include-split-exported-mps
    if parsed_version >= 840:
        assert "include-split-exported-mps" not in optimization

    # Version 8.5.0 - Added CSR fields in adequacy patch
    if parsed_version >= 850:
        adequacy = data["adequacy patch"]
        assert "price-taking-order" in adequacy
        assert "include-hurdle-cost-csr" in adequacy
        assert "check-csr-cost-function" in adequacy
        assert "threshold-initiate-curtailment-sharing-rule" in adequacy
        assert "threshold-display-local-matching-rule-violations" in adequacy
        assert "threshold-csr-variable-bounds-relaxation" in adequacy

    # Version 8.6.0 - Added enable-first-step
    if parsed_version >= 860 and parsed_version < 920:  # removed in 9.2.0
        adequacy = data["adequacy patch"]
        assert "enable-first-step" in adequacy

    # Version 9.2.0 - Added compatibility section, removed fields
    if parsed_version >= 920:
        assert "compatibility" in data
        assert "hydro-pmax" in data["compatibility"]
        assert "initial-reservoir-levels" not in other_preferences
        adequacy = data["adequacy patch"]
        assert "set-to-null-ntc-between-physical-out-for-first-step" not in adequacy
        assert "enable-first-step" not in adequacy

    # Version 9.3.0 - Removed refresh* fields
    if parsed_version >= 930:
        assert "refreshtimeseries" not in general
        assert "refreshintervalload" not in general
        assert "refreshintervalhydro" not in general
        assert "refreshintervalwind" not in general
        assert "refreshintervalthermal" not in general
        assert "refreshintervalsolar" not in general
