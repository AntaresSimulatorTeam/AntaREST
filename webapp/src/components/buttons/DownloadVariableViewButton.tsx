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
import type { VariableViewParams } from "@/services/api/studies/outputs/variableViews/types";
import type { StudyMetadata } from "@/types/types";
import { downloadFile } from "@/utils/fileUtils";
import { useTranslation } from "react-i18next";
import DownloadButton from "./DownloadButton";
import { EXPORT_FORMAT_OPTIONS, FORMAT_TO_OPTIONS, type ExportFormat } from "./exportFormatOptions";

export interface DownloadVariableViewButtonProps {
  studyId: StudyMetadata["id"];
  outputId: string;
  params: VariableViewParams;
  disabled?: boolean;
  label?: string;
}

function DownloadVariableViewButton(props: DownloadVariableViewButtonProps) {
  const { t } = useTranslation();
  const { studyId, outputId, params, disabled, label = t("global.export") } = props;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDownload = async (format: ExportFormat) => {
    const { extension, ...options } = FORMAT_TO_OPTIONS[format];

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
    <DownloadButton options={EXPORT_FORMAT_OPTIONS} onClick={handleDownload} disabled={disabled}>
      {label}
    </DownloadButton>
  );
}

export default DownloadVariableViewButton;
