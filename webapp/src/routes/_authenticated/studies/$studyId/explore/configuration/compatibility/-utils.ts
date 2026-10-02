/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import type { Options } from "@/components/fieldEditors/SelectFE";
import client from "@/services/api/client";
import type { StudyMetadata } from "@/types/types";
import type { DeepPartial } from "react-hook-form";

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const HYDRO_PMAX_OPTIONS: Options<string> = ["hourly", "daily"].map((value) => ({
  label: (t) => t(`global.time.${value}`),
  value,
}));

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface CompatibilityParamsFormFields {
  hydroPmax?: string;
}

////////////////////////////////////////////////////////////////
// API
////////////////////////////////////////////////////////////////

function makeCompatibilityRequestURL(studyId: StudyMetadata["id"]): string {
  return `v1/studies/${studyId}/config/compatibility/form`;
}

export async function getCompatibilityParamsFormFields(
  studyId: StudyMetadata["id"],
): Promise<CompatibilityParamsFormFields> {
  const { data } = await client.get<CompatibilityParamsFormFields>(
    makeCompatibilityRequestURL(studyId),
  );
  return data;
}

export async function setCompatibilityParamsFormFields(
  studyId: StudyMetadata["id"],
  values: DeepPartial<CompatibilityParamsFormFields>,
) {
  await client.put(makeCompatibilityRequestURL(studyId), values);
}
