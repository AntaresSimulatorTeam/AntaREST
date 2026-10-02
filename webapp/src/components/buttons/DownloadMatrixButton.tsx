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
import {
  EXPORT_FORMAT_OPTIONS,
  EXPORT_FORMAT_TO_OPTIONS,
  type ExportFormat,
} from "../utils/buttonOptions";
import type { Options } from "./SplitButton";

export interface DownloadMatrixButtonProps {
  studyId: StudyMetadata["id"];
  path: string;
  disabled?: boolean;
  label?: string;
}

const OPTIONS: Readonly<Options<ExportFormat | "raw">> = [
  ...EXPORT_FORMAT_OPTIONS,
  { label: (t) => t("matrix.export.format.raw"), value: "raw" },
];

function DownloadMatrixButton(props: DownloadMatrixButtonProps) {
  const { t } = useTranslation();
  const { studyId, path, disabled, label = t("global.export") } = props;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDownload = async (format: ExportFormat | "raw") => {
    if (!path) {
      return;
    }

    if (format === "raw") {
      const file = await getRawFile({ studyId, path });
      return downloadFile(file, file.name);
    }

    const { extension, ...options } = EXPORT_FORMAT_TO_OPTIONS[format];

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
