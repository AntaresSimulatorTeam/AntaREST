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

import { getMatrixFile, getRawFile } from "@/services/api/studies/raw";
import { downloadFile } from "@/utils/fileUtils";
import type { StudyMetadata } from "@/types/types";
import { useTranslation } from "react-i18next";
import DownloadButton from "./DownloadButton";
import type { TableExportFormatValue } from "@/services/api/studies/raw/types";
import type { Options } from "./SplitButton";

type ExportFormat =
  | "csv"
  | "csv (semicolon)"
  | "csv (header)"
  | "csv (semicolon header)"
  | "xlsx"
  | "raw";

export interface DownloadMatrixButtonProps {
  studyId: StudyMetadata["id"];
  path: string;
  disabled?: boolean;
  label?: string;
}

const OPTIONS: Readonly<Options<ExportFormat>> = [
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
  { label: (t) => t("matrix.export.format.raw"), value: "raw" },
];

const formatToOptions: Record<
  Exclude<ExportFormat, "raw">,
  { format: TableExportFormatValue; header: boolean; index: boolean; extension: string }
> = {
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
} as const;

function DownloadMatrixButton(props: DownloadMatrixButtonProps) {
  const { t } = useTranslation();
  const { studyId, path, disabled, label = t("global.export") } = props;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDownload = async (format: ExportFormat) => {
    if (!path) {
      return;
    }

    if (format === "raw") {
      const file = await getRawFile({ studyId, path });
      return downloadFile(file, file.name);
    }

    const { extension, ...options } = formatToOptions[format];

    const matrixFile = await getMatrixFile({
      ...options,
      studyId,
      path,
    });

    return downloadFile(matrixFile, `matrix_${studyId}_${path.replace("/", "_")}.${extension}`);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DownloadButton options={OPTIONS} onClick={handleDownload} disabled={!path || disabled}>
      {label}
    </DownloadButton>
  );
}

export default DownloadMatrixButton;
