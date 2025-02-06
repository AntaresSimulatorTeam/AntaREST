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

import logging
from pathlib import Path

import click

from antarest.tools.admin_lib import clean_locks as do_clean_locks
from antarest.tools.admin_lib import reindex_table as do_reindex_table

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def commands() -> None:
    pass


@commands.command()
@click.option(
    "--config",
    "-c",
    nargs=1,
    required=True,
    type=click.Path(exists=True),
    help="Application config",
)
def clean_locks(config: str) -> None:
    """Clean app locks"""
    do_clean_locks(Path(config))


@commands.command()
@click.option(
    "--config",
    "-c",
    nargs=1,
    required=True,
    type=click.Path(exists=True),
    help="Application config",
)
def reindex_tables(config: str) -> None:
    """Clean app locks"""
    do_reindex_table(Path(config))


if __name__ == "__main__":
    commands()
