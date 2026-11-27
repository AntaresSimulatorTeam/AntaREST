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

import type { Translate } from "../buildReportDocument";
import { buildReportFileName } from "../buildReportFileName";

const translate: Translate = (key, options = {}) => `${key}:${options.study},${options.date}`;

const CHECKED_AT = new Date("2026-11-27T14:05:00Z");

describe("buildReportFileName", () => {
  test("names the file after the study and the day of the report", () => {
    expect(buildReportFileName("Reference 2030", CHECKED_AT, translate)).toBe(
      "study.check.pdf.fileName:Reference-2030,2026-11-27.pdf",
    );
  });

  test("keeps the accented letters of the name of the study", () => {
    expect(buildReportFileName("Référence été", CHECKED_AT, translate)).toBe(
      "study.check.pdf.fileName:Référence-été,2026-11-27.pdf",
    );
  });

  test("leaves out the characters a file name cannot have", () => {
    expect(buildReportFileName('BP2030 / hiver: "froid"?', CHECKED_AT, translate)).toBe(
      "study.check.pdf.fileName:BP2030-hiver-froid,2026-11-27.pdf",
    );
  });
});
