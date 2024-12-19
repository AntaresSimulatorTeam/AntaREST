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

import { getMatrixFile } from "../../../services/api/studies/raw";
import { downloadFile } from "../../../utils/fileUtils";
import { StudyMetadata } from "../../../common/types";
import { useTranslation } from "react-i18next";
import DownloadButton from "./DownloadButton";
import type { TTableExportFormat } from "@/services/api/studies/raw/types";

export interface DownloadMatrixButtonProps {
  studyId: StudyMetadata["id"];
  path: string;
  disabled?: boolean;
  label?: string;
}

function DownloadMatrixButton(props: DownloadMatrixButtonProps) {
  const { t } = useTranslation();
  const { studyId, path, disabled, label = t("global.export") } = props;

  const options: Array<{ label: string; value: TTableExportFormat }> = [
    { label: "CSV", value: "csv" },
    {
      label: `CSV (${t("global.semicolon").toLowerCase()})`,
      value: "csv (semicolon)",
    },
    { label: "TSV", value: "tsv" },
    { label: "XLSX", value: "xlsx" },
  ];

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDownload = async (format: TTableExportFormat) => {
    if (!path) {
      return;
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

    return downloadFile(
      matrixFile,
      `matrix_${studyId}_${path.replace("/", "_")}.${extension}`,
    );
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DownloadButton
      formatOptions={options}
      onClick={handleDownload}
      disabled={!path || disabled}
    >
      {label}
    </DownloadButton>
  );
}

export default DownloadMatrixButton;
