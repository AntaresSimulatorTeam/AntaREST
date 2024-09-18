/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import FileUploadIcon from "@mui/icons-material/FileUpload";
import SplitButton from "./buttons/SplitButton.tsx";
import { downloadMatrix } from "../../services/api/studies/raw/index.ts";
import { downloadFile } from "../../utils/fileUtils.ts";
import { useState } from "react";
import { StudyMetadata } from "../../common/types.ts";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar.tsx";
import { useTranslation } from "react-i18next";

export interface DownloadMatrixButtonProps {
  studyId: StudyMetadata["id"];
  path?: string;
  disabled?: boolean;
  label?: string;
}

const EXPORT_OPTIONS = [
  { label: "TSV", value: "tsv" },
  { label: "Excel", value: "xlsx" },
] as const;

type ExportFormat = (typeof EXPORT_OPTIONS)[number]["value"];

function DownloadMatrixButton(props: DownloadMatrixButtonProps) {
  const { t } = useTranslation();
  const { studyId, path, disabled, label = t("global.export") } = props;
  const [isDownloading, setIsDownloading] = useState(false);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDownload = async (format: ExportFormat) => {
    if (!path) {
      return;
    }

    setIsDownloading(true);

    const isExcel = format === "xlsx";

    try {
      const res = await downloadMatrix({
        studyId,
        path,
        format,
        header: isExcel,
        index: isExcel,
      });

      downloadFile(
        res,
        `matrix_${studyId}_${path.replace("/", "_")}.${format}`,
      );
    } catch (err) {
      enqueueErrorSnackbar(t("global.download.error"), String(err));
    }

    setIsDownloading(false);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitButton
      variant="contained"
      options={[...EXPORT_OPTIONS]}
      onClick={handleDownload}
      size="small"
      disabled={!path || disabled}
      ButtonProps={{
        startIcon: <FileUploadIcon />,
        loadingPosition: "start",
        loading: isDownloading,
      }}
    >
      {label}
    </SplitButton>
  );
}

export default DownloadMatrixButton;
