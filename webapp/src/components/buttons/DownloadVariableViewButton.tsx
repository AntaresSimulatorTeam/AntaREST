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

import { exportVariableViewData } from "@/services/api/studies/outputs/variableViews";
import type {
  VariableViewExportFormat,
  VariableViewParams,
} from "@/services/api/studies/outputs/variableViews/types";
import type { StudyMetadata } from "@/types/types";
import { downloadFile } from "@/utils/fileUtils";
import { useTranslation } from "react-i18next";
import DownloadButton from "./DownloadButton";
import type { Options } from "./SplitButton";

type ExportFormat = "csv" | "csv (semicolon)" | "csv (header)" | "csv (semicolon header)" | "xlsx";

export interface DownloadVariableViewButtonProps {
  studyId: StudyMetadata["id"];
  outputId: string;
  params: VariableViewParams;
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
];

const formatToOptions: Record<
  ExportFormat,
  { format: VariableViewExportFormat; header: boolean; index: boolean; extension: string }
> = {
  csv: { format: "csv", header: false, index: true, extension: "csv" },
  "csv (header)": { format: "csv", header: true, index: true, extension: "csv" },
  "csv (semicolon)": { format: "csv (semicolon)", header: true, index: false, extension: "csv" },
  "csv (semicolon header)": {
    format: "csv (semicolon)",
    header: true,
    index: true,
    extension: "csv",
  },
  xlsx: { format: "xlsx", header: true, index: true, extension: "xlsx" },
} as const;

function DownloadVariableViewButton(props: DownloadVariableViewButtonProps) {
  const { t } = useTranslation();
  const { studyId, outputId, params, disabled, label = t("global.export") } = props;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDownload = async (format: ExportFormat) => {
    const { extension, ...options } = formatToOptions[format];

    const blob = await exportVariableViewData({
      studyId,
      outputId,
      params,
      ...options,
    });

    const filename = `variable_${params.variableName}_${params.frequency}.${extension}`;
    downloadFile(blob, filename);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DownloadButton options={OPTIONS} onClick={handleDownload} disabled={disabled}>
      {label}
    </DownloadButton>
  );
}

export default DownloadVariableViewButton;
