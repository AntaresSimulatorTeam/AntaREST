/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { Column } from "../../../shared/constants";
import { createColumn, createNumericColumn } from "./utils";

export const COLUMNS = {
  mixed: [
    createColumn("text", Column.Text),
    createColumn("date", Column.DateTime),
    createNumericColumn("num1"),
    createNumericColumn("num2"),
    createColumn("agg", Column.Aggregate),
  ],
  nonData: [createColumn("text", Column.Text), createColumn("date", Column.DateTime)],
  dataOnly: [createNumericColumn("num1"), createNumericColumn("num2")],
};
