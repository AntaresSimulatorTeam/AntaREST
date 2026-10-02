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

import DownloadButton from "@/components/buttons/DownloadButton";
import {
  EXPORT_FORMAT_OPTIONS,
  EXPORT_FORMAT_TO_OPTIONS,
  type ExportFormat,
} from "@/components/utils/buttonOptions";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { exportVariableViewData } from "@/services/api/studies/outputs/variableViews";
import type { VariableViewParams } from "@/services/api/studies/outputs/variableViews/types";
import { downloadFile } from "@/utils/fileUtils";
import { useTranslation } from "react-i18next";
import useOutput from "../../../-hooks/useOutput";

export interface DownloadVariableViewButtonProps {
  params: VariableViewParams;
  disabled?: boolean;
  label?: string;
}

const variableViewParamsToFilenameSuffix = (params: VariableViewParams) => {
  switch (params.type) {
    case "area":
      return `area_${params.areaId}`;
    case "link":
      return `link_${params.areaFromId}_${params.areaToId}`;
    case "thermal":
    case "renewable":
    case "st_storage":
      return `${params.type}_${params.areaId}_${params.clusterId}`;
    default: {
      return "";
    }
  }
};

function DownloadVariableViewButton(props: DownloadVariableViewButtonProps) {
  const { t } = useTranslation();
  const { params, disabled, label = t("global.export") } = props;
  const study = useStudy();
  const output = useOutput();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDownload = async (format: ExportFormat) => {
    const { extension, ...options } = EXPORT_FORMAT_TO_OPTIONS[format];

    const blob = await exportVariableViewData({
      studyId: study.id,
      outputId: output.id,
      params,
      ...options,
    });

    const outputArea = variableViewParamsToFilenameSuffix(params);
    const filename = `matrix_${study.id}_output_${output.id}_${outputArea}_${params.variableName}_${params.frequency}.${extension}`;

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
