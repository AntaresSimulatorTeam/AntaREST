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
    python -m tests.study.dao.bench_database_xpansion_dao \\
        --db-url "postgresql://USER:PASS@localhost/antarest_bench" [-n ITERATIONS] [--warmup N]

Usage (pytest, smoke-level):
    pytest tests/study/dao/bench_database_xpansion_dao.py -v -s
"""

import argparse
import gc
import statistics
import time
import uuid
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
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
from antarest.study.model import STUDY_VERSION_8_8, StorageMode, Study
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from tests.helpers import create_study

# ---------------------------------------------------------------------------
# Infrastructure helpers
# ---------------------------------------------------------------------------

_DEFAULT_DB_URL = "postgresql://antarest:antarest@localhost/antarest_bench"


def _build_engine(db_url: str):
    # Use a small pool — mirrors a real application setup.
    engine = create_engine(db_url, pool_size=5, max_overflow=0)

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
        generator_matrix_constants = GeneratorMatrixConstants(matrix_service)
        factory = DatabaseStudyDaoFactory(matrix_service, generator_matrix_constants, session=session)
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

    # with timer.measure("delete_xpansion_candidate"):
    #     dao.delete_xpansion_candidate("backup_link")

    # with timer.measure("delete_xpansion_configuration"):
    #     dao.delete_xpansion_configuration()


# ---------------------------------------------------------------------------
# Timer
# ---------------------------------------------------------------------------


def _trimmed_mean(samples: list[float], cut: float = 0.05) -> float:
    """Mean after dropping the bottom `cut` and top `cut` fraction of samples."""
    s = sorted(samples)
    k = int(len(s) * cut)
    trimmed = s[k : len(s) - k] if k > 0 else s
    return statistics.mean(trimmed)


def _make_stats(samples: list[float]) -> dict:
    return {
        "n": len(samples),
        "mean_ms": statistics.mean(samples) * 1_000,
        "tmean_ms": _trimmed_mean(samples) * 1_000,
        "median_ms": statistics.median(samples) * 1_000,
        "stdev_ms": statistics.stdev(samples) * 1_000 if len(samples) > 1 else 0.0,
        "min_ms": min(samples) * 1_000,
        "max_ms": max(samples) * 1_000,
        "total_ms": sum(samples) * 1_000,
    }


class Timer:
    def __init__(self) -> None:
        self._buckets: dict[str, list[float]] = {}

    @contextmanager
    def measure(self, name: str) -> Generator[None, None, None]:
        t0 = time.perf_counter()
        yield
        self._buckets.setdefault(name, []).append(time.perf_counter() - t0)

    def stats(self) -> dict[str, dict]:
        return {name: _make_stats(s) for name, s in self._buckets.items()}


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------


def _populate_background_data(make_session, matrix_service: InMemorySimpleMatrixService, n: int) -> list[str]:
    """Insert n xpansion configurations with 3 candidates each. Returns study IDs for later cleanup."""
    study_ids = []
    for i in range(n):
        session = make_session()
        dao = _build_dao(session, matrix_service)
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.create_xpansion_configuration()
        dao.save_xpansion_candidate(_candidate(f"bg_cand_{i}_a", "lyon", "paris"))
        dao.save_xpansion_candidate(_candidate(f"bg_cand_{i}_b", "lyon", "paris", cost=2_000.0))
        dao.save_xpansion_candidate(_candidate(f"bg_cand_{i}_c", "lyon", "paris", cost=500.0))
        study_ids.append(dao.get_study_id())
        session.close()
    return study_ids


def _delete_all(
    make_session, matrix_service: InMemorySimpleMatrixService, study_ids: list[str], timer: "Timer"
) -> None:
    """Delete all xpansion configurations — runs after all scenarios are created."""
    for study_id in study_ids:
        session = make_session()
        generator_matrix_constants = GeneratorMatrixConstants(matrix_service)
        factory = DatabaseStudyDaoFactory(matrix_service, generator_matrix_constants, session=session)
        study = session.get(Study, study_id)
        dao = factory.create_study_dao(study)
        with timer.measure("delete_xpansion_configuration"):
            dao.delete_xpansion_configuration()
        session.close()


def run_benchmark(
    iterations: int, db_url: str = _DEFAULT_DB_URL, warmup: int = 50, background_rows: int = 1_000
) -> dict[str, dict]:
    engine = _build_engine(db_url)
    matrix_service = InMemorySimpleMatrixService()
    make_session = sessionmaker(bind=engine)

    _null_timer = Timer()  # discarded — absorbs warmup allocations

    gc.collect()
    gc.disable()
    try:
        # Populate background data so operations run against non-empty tables.
        if background_rows:
            print(f"Inserting {background_rows} background rows…")
            background_study_ids = _populate_background_data(make_session, matrix_service, background_rows)
        else:
            background_study_ids = []

        # Warmup: prime SQLAlchemy's statement cache and the connection pool.
        for _ in range(warmup):
            session = make_session()
            dao = _build_dao(session, matrix_service)
            _run_scenario(dao, _null_timer)
            session.close()

        # Measurement: create all scenarios without deleting.
        timer = Timer()
        scenario_times: list[float] = []
        measurement_study_ids: list[str] = []
        for _ in range(iterations):
            session = make_session()
            dao = _build_dao(session, matrix_service)

            t0 = time.perf_counter()
            _run_scenario(dao, timer)
            scenario_times.append(time.perf_counter() - t0)

            measurement_study_ids.append(dao.get_study_id())
            session.close()

        # Delete all — background + measurement — against a full table.
        all_study_ids = background_study_ids + measurement_study_ids
        _delete_all(make_session, matrix_service, all_study_ids, timer)
    finally:
        gc.enable()

    Base.metadata.drop_all(engine)
    engine.dispose()

    stats = timer.stats()
    stats["[scenario total]"] = _make_stats(scenario_times)
    return stats


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

_COL = 48


def print_results(stats: dict[str, dict]) -> None:
    header = (
        f"{'Operation':<{_COL}} {'n':>6}  {'mean':>9}  {'t.mean':>9}  {'median':>9}  {'cv':>7}  "
        f"{'min':>9}  {'max':>9}  {'total':>11}"
    )
    sep = f"{'-' * _COL} {'-' * 6}  {'-' * 9}  {'-' * 9}  {'-' * 9}  {'-' * 7}  {'-' * 9}  {'-' * 9}  {'-' * 11}"
    print(f"\n{header}\n{sep}")

    for name, s in stats.items():
        indent = "" if name.startswith("[") else "  "
        label = f"{indent}{name}"
        cv = s["stdev_ms"] / s["mean_ms"] * 100 if s["mean_ms"] > 0 else 0.0
        print(
            f"{label:<{_COL}} "
            f"{s['n']:>6}  "
            f"{s['mean_ms']:>8.3f}ms  "
            f"{s['tmean_ms']:>8.3f}ms  "
            f"{s['median_ms']:>8.3f}ms  "
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
    parser = argparse.ArgumentParser(description="Benchmark DatabaseXpansionDao")
    parser.add_argument("-n", "--iterations", type=int, default=2_000, help="Number of iterations (default: 2000)")
    parser.add_argument("--warmup", type=int, default=50, help="Warmup iterations, not measured (default: 50)")
    parser.add_argument(
        "--background-rows", type=int, default=1_000, help="Background configs pre-inserted (default: 1000)"
    )
    parser.add_argument(
        "--db-url",
        default=_DEFAULT_DB_URL,
        help=f"SQLAlchemy DB URL (default: {_DEFAULT_DB_URL})",
    )
    args = parser.parse_args()

    print(f"DB              : {args.db_url}")
    print(f"Background rows : {args.background_rows}")
    print(f"Warmup          : {args.warmup}")
    print(f"Runs            : {args.iterations}")
    stats = run_benchmark(
        iterations=args.iterations, db_url=args.db_url, warmup=args.warmup, background_rows=args.background_rows
    )
    print_results(stats)
