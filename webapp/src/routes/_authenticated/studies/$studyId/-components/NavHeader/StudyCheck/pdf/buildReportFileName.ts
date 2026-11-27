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

import { format } from "date-fns";
import type { Translate } from "./buildReportDocument";

const CHARACTERS_UNSAFE_IN_A_FILE_NAME = /[^\p{L}\p{N}._-]+/gu;
const LEADING_OR_TRAILING_DASHES = /^-+|-+$/g;

/**
 * Names the PDF report of a check after the study and the day of the report.
 *
 * @param studyName - Name of the study which was checked.
 * @param date - When the report is generated.
 * @param t - Translation function, in the language of the report.
 * @returns The name of the file, with its extension.
 */
export function buildReportFileName(studyName: string, date: Date, t: Translate): string {
  const study = studyName
    .replace(CHARACTERS_UNSAFE_IN_A_FILE_NAME, "-")
    .replace(LEADING_OR_TRAILING_DASHES, "");

  return `${t("study.check.pdf.fileName", { study, date: format(date, "yyyy-MM-dd") })}.pdf`;
}
