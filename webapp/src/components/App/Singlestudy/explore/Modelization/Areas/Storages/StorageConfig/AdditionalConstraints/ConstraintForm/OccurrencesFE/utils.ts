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

import i18n from "@/i18n";
import type { AdditionalConstraintOccurrences } from "@/services/api/studies/areas/storages/types";
import { isOccurrencesValid } from "../utils";

export function validateOccurrences(v: AdditionalConstraintOccurrences): string | true {
  if (!isOccurrencesValid(v)) {
    return i18n.t("study.modelization.storages.additionalConstraints.occurrences.noEmpty");
  }
  return true;
}
