/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import * as R from "ramda";
import * as RA from "ramda-adjunct";

export const getCellType = R.cond([
  [RA.isNumber, R.always("numeric")],
  [RA.isBoolean, R.always("checkbox")],
  [R.T, R.always("text")],
]);
