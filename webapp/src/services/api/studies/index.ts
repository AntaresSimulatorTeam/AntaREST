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

import snakeCase from "lodash/snakeCase";
import * as RA from "ramda-adjunct";
import client from "../client";
import type { CopyStudyParams } from "./types";

export async function copyStudy({ studyId, ...params }: CopyStudyParams) {
  const { data } = await client.post<string>(`/v1/studies/${studyId}/copy`, null, {
    params: RA.renameKeysWith(snakeCase, params),
  });
  return data;
}
