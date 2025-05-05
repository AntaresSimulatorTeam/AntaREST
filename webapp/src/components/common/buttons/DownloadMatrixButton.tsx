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

import { getMatrixFile, getRawFile } from "@/services/api/studies/raw";
import { downloadFile } from "@/utils/fileUtils";
import type { StudyMetadata } from "@/types/types";
import { useTranslation } from "react-i18next";
import DownloadButton from "./DownloadButton";
import type { TableExportFormatValue } from "@/services/api/studies/raw/types";

type ExportFormat = TableExportFormatValue | "raw";

export interface DownloadMatrixButtonProps {
  studyId: StudyMetadata["id"];
  path: string;
  disabled?: boolean;
  label?: string;
}

function DownloadMatrixButton(props: DownloadMatrixButtonProps) {
  const { t } = useTranslation();
  const { studyId, path, disabled, label = t("global.export") } = props;

  const options: Array<{ label: string; value: ExportFormat }> = [
    { label: "CSV", value: "csv" },
    {
      label: `CSV (${t("global.semicolon").toLowerCase()})`,
      value: "csv (semicolon)",
    },
    { label: "TSV", value: "tsv" },
    { label: "XLSX", value: "xlsx" },
    { label: `${t("global.rawFile")}`, value: "raw" },
  ];

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

    const isXlsx = format === "xlsx";

    const matrixFile = await getMatrixFile({
      studyId,
      path,
      format,
      header: isXlsx,
      index: isXlsx,
    });

    const extension = format === "csv (semicolon)" ? "csv" : format;

    return downloadFile(matrixFile, `matrix_${studyId}_${path.replace("/", "_")}.${extension}`);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DownloadButton formatOptions={options} onClick={handleDownload} disabled={!path || disabled}>
      {label}
    </DownloadButton>
  );
}

export default DownloadMatrixButton;
