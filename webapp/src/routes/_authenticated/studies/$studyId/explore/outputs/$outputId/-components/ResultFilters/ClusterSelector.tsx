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

import StringFE from "@/components/fieldEditors/StringFE";
import type { VariablesListDTO } from "@/services/api/studies/outputs/variableViews/types";
import { Autocomplete } from "@mui/material";
import { useEffect, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { getClusters, getFirstClusterId, type ClusterOption, type DataType } from "../../-utils";

interface ClusterSelectorProps {
  variablesMetadata: VariablesListDTO | null;
  dataType: DataType;
  selectedItemId: string;
  selectedClusterId: string;
  onClusterSelect: (clusterId: string) => void;
  disabled?: boolean;
}

function ClusterSelector({
  variablesMetadata,
  dataType,
  selectedItemId,
  selectedClusterId,
  onClusterSelect,
  disabled,
}: ClusterSelectorProps) {
  const { t } = useTranslation();

  const clusterOptions = useMemo(() => {
    if (!variablesMetadata || !selectedItemId) {
      return [];
    }

    return getClusters(variablesMetadata, selectedItemId, dataType);
  }, [variablesMetadata, dataType, selectedItemId]);

  const isClusterValid = clusterOptions.some((c) => c.name === selectedClusterId);

  // Auto-select first cluster when switching data types or when no valid cluster is selected
  useEffect(() => {
    if (!isClusterValid && variablesMetadata && selectedItemId) {
      const firstClusterId = getFirstClusterId(variablesMetadata, selectedItemId, dataType);

      if (firstClusterId) {
        onClusterSelect(firstClusterId);
      }
    }
  }, [isClusterValid, variablesMetadata, selectedItemId, dataType, onClusterSelect]);

  const getLabel = () => {
    switch (dataType) {
      case "details":
        return t("study.results.thermalCluster");
      case "details-res":
        return t("study.results.renewableCluster");
      case "details-STstorage":
        return t("study.results.shortTermStorage");
      default:
        return t("study.results.cluster");
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Autocomplete
      size="extra-small"
      options={clusterOptions}
      getOptionLabel={(option: ClusterOption) => option.name}
      value={clusterOptions.find((c) => c.name === selectedClusterId) || null}
      onChange={(_event, newValue) => {
        onClusterSelect(newValue?.name || "");
      }}
      disabled={disabled || clusterOptions.length === 0}
      renderInput={(params) => (
        <StringFE
          {...params}
          label={getLabel()}
          margin="dense"
          size="extra-small"
          sx={{ minWidth: 160 }}
        />
      )}
      noOptionsText={t("study.results.noClusters")}
    />
  );
}

export default ClusterSelector;
