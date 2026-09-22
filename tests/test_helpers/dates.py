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
from datetime import datetime, timezone


def utc_to_local(date_str: str) -> str:
    """
    Converts a UTC date string such as "20201014-1222" to a local date string such as "20201014-1422".

    Can be useful when expected dates depend on the locale where tests are run.
    """
    utc_date = datetime.strptime(date_str, "%Y%m%d-%H%M").replace(tzinfo=timezone.utc)
    return utc_date.astimezone().strftime("%Y%m%d-%H%M")
