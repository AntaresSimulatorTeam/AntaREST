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

import type { TableExportFormatValue } from "@/services/api/studies/raw/types";
import type { Options } from "./SplitButton";

export type ExportFormat =
  | "csv"
  | "csv (semicolon)"
  | "csv (header)"
  | "csv (semicolon header)"
  | "xlsx";

export interface ExportFormatOptions {
  format: TableExportFormatValue;
  header: boolean;
  index: boolean;
  extension: string;
}

export const EXPORT_FORMAT_OPTIONS: Readonly<Options<ExportFormat>> = [
  { label: (t) => t("matrix.export.format.csv"), value: "csv" },
  { label: (t) => t("matrix.export.format.csvWithHeader"), value: "csv (header)" },
  {
    label: (t) => t("matrix.export.format.csvSemicolon"),
    value: "csv (semicolon)",
  },
  {
    label: (t) => t("matrix.export.format.csvSemicolonWithHeader"),
    value: "csv (semicolon header)",
  },
  { label: (t) => t("matrix.export.format.xlsx"), value: "xlsx" },
];

export const FORMAT_TO_OPTIONS: Record<ExportFormat, ExportFormatOptions> = {
  csv: { format: "csv", header: false, index: false, extension: "csv" },
  "csv (header)": { format: "csv", header: true, index: false, extension: "csv" },
  "csv (semicolon)": { format: "csv (semicolon)", header: false, index: false, extension: "csv" },
  "csv (semicolon header)": {
    format: "csv (semicolon)",
    header: true,
    index: false,
    extension: "csv",
  },
  xlsx: { format: "xlsx", header: true, index: true, extension: "xlsx" },
};
