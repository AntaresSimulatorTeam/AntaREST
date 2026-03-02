# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
"""
Benchmark for DatabaseXpansionDao — realistic end-to-end user workflow.

Scenario per iteration
----------------------
  1.  save_area ×2                          (setup for adequacy patterns)
  2.  create_xpansion_configuration
  3.  get_xpansion_settings
  4.  save_xpansion_settings  (no projection)
  5.  save_xpansion_candidate ×3
  6.  get_all_xpansion_candidates
  7.  get_xpansion_candidate
  8.  save_xpansion_candidate  (rename)
  9.  save_xpansion_settings   (with projection on 2 candidates)
  10. checks_xpansion_candidate_can_be_deleted  (candidate NOT in projection)
  11. save_xpansion_adequacy_criterion  (2 area patterns)
  12. get_xpansion_adequacy_criterion
  13. save_xpansion_adequacy_criterion  (replace — 1 pattern)
  14. get_xpansion_settings  (re-read)
  15. delete_xpansion_candidate
  16. delete_xpansion_configuration

Usage (standalone — run from project root):
    python -m tests.study.dao.bench_database_xpansion_dao [iterations]

Usage (pytest, smoke-level):
    pytest tests/study/dao/bench_database_xpansion_dao.py -v -s
"""

import statistics
import sys
import time
import uuid
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from antarest.dbmodel import Base
from antarest.matrixstore.in_memory import InMemorySimpleMatrixService
from antarest.study.business.model.xpansion_model import (
    XpansionAdequacyCriterion,
    XpansionAdequacyPattern,
    XpansionCandidate,
    XpansionSensitivitySettings,
    XpansionSettings,
)
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.database_study_factory_dao import DatabaseStudyDaoFactory
from antarest.study.model import STUDY_VERSION_8_8, StorageMode
from tests.helpers import create_study

# ---------------------------------------------------------------------------
# Infrastructure helpers
# ---------------------------------------------------------------------------


def _build_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return engine


def _build_dao(session: Session, matrix_service: InMemorySimpleMatrixService) -> DatabaseStudyDao:
    study_id = str(uuid.uuid4())
    with session:
        study = create_study(id=study_id, name="Bench Study", version=str(STUDY_VERSION_8_8))
        study.storage_mode = StorageMode.DATABASE
        session.add(study)
        session.commit()
        factory = DatabaseStudyDaoFactory(matrix_service, session)
        return factory.create_study_dao(study)


def _candidate(name: str, area_from: str, area_to: str, cost: float = 1_000.0) -> XpansionCandidate:
    return XpansionCandidate(
        name=name,
        link=f"{area_from} - {area_to}",
        annual_cost_per_mw=cost,
        max_investment=5_000.0,
    )


# ---------------------------------------------------------------------------
# Scenario
# ---------------------------------------------------------------------------


def _run_scenario(dao: DatabaseStudyDao, timer: "Timer") -> None:
    """Full end-to-end Xpansion workflow that mirrors realistic API usage."""

    with timer.measure("save_area ×2"):
        dao.save_area("Paris")
        dao.save_area("Lyon")

    with timer.measure("create_xpansion_configuration"):
        dao.create_xpansion_configuration()

    with timer.measure("get_xpansion_settings"):
        dao.get_xpansion_settings()

    with timer.measure("save_xpansion_settings (no projection)"):
        dao.save_xpansion_settings(XpansionSettings(optimality_gap=10.0, log_level=1, batch_size=48))

    with timer.measure("save_xpansion_candidate ×3"):
        dao.save_xpansion_candidate(_candidate("north_south", "lyon", "paris"))
        dao.save_xpansion_candidate(_candidate("east_hub", "lyon", "paris", cost=2_000.0))
        dao.save_xpansion_candidate(_candidate("backup_link", "lyon", "paris", cost=500.0))

    with timer.measure("get_all_xpansion_candidates"):
        dao.get_all_xpansion_candidates()

    with timer.measure("get_xpansion_candidate"):
        dao.get_xpansion_candidate("north_south")

    with timer.measure("save_xpansion_candidate (rename)"):
        dao.save_xpansion_candidate(
            _candidate("north_south_v2", "lyon", "paris", cost=1_500.0),
            old_id="north_south",
        )

    with timer.measure("save_xpansion_settings (with projection)"):
        dao.save_xpansion_settings(
            XpansionSettings(
                optimality_gap=5.0,
                sensitivity_config=XpansionSensitivitySettings(
                    epsilon=50.0,
                    capex=True,
                    projection=["east_hub", "north_south_v2"],
                ),
            )
        )

    with timer.measure("checks_xpansion_candidate_can_be_deleted"):
        dao.checks_xpansion_candidate_can_be_deleted("backup_link")

    with timer.measure("save_xpansion_adequacy_criterion (2 patterns)"):
        dao.save_xpansion_adequacy_criterion(
            XpansionAdequacyCriterion(
                stopping_threshold=1_000.0,
                criterion_count_threshold=3.0,
                patterns=[
                    XpansionAdequacyPattern(area="paris", criterion=0.95),
                    XpansionAdequacyPattern(area="lyon", criterion=0.80),
                ],
            )
        )

    with timer.measure("get_xpansion_adequacy_criterion"):
        dao.get_xpansion_adequacy_criterion()

    with timer.measure("save_xpansion_adequacy_criterion (1 pattern)"):
        dao.save_xpansion_adequacy_criterion(
            XpansionAdequacyCriterion(
                stopping_threshold=800.0,
                patterns=[XpansionAdequacyPattern(area="paris", criterion=0.90)],
            )
        )

    with timer.measure("get_xpansion_settings (re-read)"):
        dao.get_xpansion_settings()

    with timer.measure("delete_xpansion_candidate"):
        dao.delete_xpansion_candidate("backup_link")

    with timer.measure("delete_xpansion_configuration"):
        dao.delete_xpansion_configuration()


# ---------------------------------------------------------------------------
# Timer
# ---------------------------------------------------------------------------


class Timer:
    def __init__(self) -> None:
        self._buckets: dict[str, list[float]] = {}

    @contextmanager
    def measure(self, name: str) -> Generator[None, None, None]:
        t0 = time.perf_counter()
        yield
        self._buckets.setdefault(name, []).append(time.perf_counter() - t0)

    def stats(self) -> dict[str, dict]:
        return {
            name: {
                "n": len(s),
                "mean_ms": statistics.mean(s) * 1_000,
                "stdev_ms": statistics.stdev(s) * 1_000 if len(s) > 1 else 0.0,
                "min_ms": min(s) * 1_000,
                "max_ms": max(s) * 1_000,
                "total_ms": sum(s) * 1_000,
            }
            for name, s in self._buckets.items()
        }


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------


def run_benchmark(iterations: int) -> dict[str, dict]:
    engine = _build_engine()
    matrix_service = InMemorySimpleMatrixService()
    make_session = sessionmaker(bind=engine)

    timer = Timer()
    scenario_times: list[float] = []

    for _ in range(iterations):
        session = make_session()
        dao = _build_dao(session, matrix_service)

        t0 = time.perf_counter()
        _run_scenario(dao, timer)
        scenario_times.append(time.perf_counter() - t0)

        session.close()

    engine.dispose()

    stats = timer.stats()
    stats["[scenario total]"] = {
        "n": len(scenario_times),
        "mean_ms": statistics.mean(scenario_times) * 1_000,
        "stdev_ms": statistics.stdev(scenario_times) * 1_000 if len(scenario_times) > 1 else 0.0,
        "min_ms": min(scenario_times) * 1_000,
        "max_ms": max(scenario_times) * 1_000,
        "total_ms": sum(scenario_times) * 1_000,
    }
    return stats


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

_COL = 48


def print_results(stats: dict[str, dict]) -> None:
    header = f"{'Operation':<{_COL}} {'n':>6}  {'mean':>9}  {'cv':>7}  {'min':>9}  {'max':>9}  {'total':>11}"
    sep = f"{'-' * _COL} {'-' * 6}  {'-' * 9}  {'-' * 7}  {'-' * 9}  {'-' * 9}  {'-' * 11}"
    print(f"\n{header}\n{sep}")

    for name, s in stats.items():
        indent = "" if name.startswith("[") else "  "
        label = f"{indent}{name}"
        cv = s["stdev_ms"] / s["mean_ms"] * 100 if s["mean_ms"] > 0 else 0.0
        print(
            f"{label:<{_COL}} "
            f"{s['n']:>6}  "
            f"{s['mean_ms']:>8.3f}ms  "
            f"{cv:>6.1f}%  "
            f"{s['min_ms']:>8.3f}ms  "
            f"{s['max_ms']:>8.3f}ms  "
            f"{s['total_ms']:>10.1f}ms"
        )
    print()


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2_000
    print(f"Running {n} iterations …")
    print("(run as: python -m tests.study.dao.bench_database_xpansion_dao [N])")
    stats = run_benchmark(iterations=n)
    print_results(stats)
