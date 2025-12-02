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

import { Autocomplete } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import StringFE from "@/components/common/fieldEditors/StringFE";
import type { VariablesListDTO } from "@/services/api/studies/outputs/variableViews/types";
import type { DataType, MonteCarloMode, OutputItemType } from "../utils";

interface VariableSelectorProps {
  variablesMetadata: VariablesListDTO | null;
  mcMode: MonteCarloMode;
  dataType: DataType;
  itemType: OutputItemType;
  selectedItemId: string;
  selectedVariable: string;
  onVariableSelect: (variable: string) => void;
  disabled?: boolean;
}

interface VariableOption {
  variable: string;
}

function VariableSelector({
  variablesMetadata,
  mcMode,
  dataType,
  itemType,
  selectedItemId,
  selectedVariable,
  onVariableSelect,
  disabled,
}: VariableSelectorProps) {
  const { t } = useTranslation();

  const variableOptions = useMemo(() => {
    if (!variablesMetadata || !selectedItemId) {
      return [];
    }

    const data = mcMode === "mc-all" ? variablesMetadata.mcAll : variablesMetadata.mcInd;
    const options: VariableOption[] = [];

    if (itemType === "areas") {
      const area = data.areas.find((a) => a.name === selectedItemId);
      if (!area) {
        return [];
      }

      if (dataType === "values") {
        area.variables.forEach((variable) => {
          options.push({ variable });
        });
      } else if (dataType === "details") {
        area.thermalClusters?.forEach((cluster) => {
          cluster.variables.forEach((variable) => {
            options.push({ variable });
          });
        });
      } else if (dataType === "details-res") {
        area.renewableClusters?.forEach((cluster) => {
          cluster.variables.forEach((variable) => {
            options.push({ variable });
          });
        });
      } else if (dataType === "details-STstorage") {
        area.shortTermStorages?.forEach((storage) => {
          storage.variables.forEach((variable) => {
            options.push({ variable });
          });
        });
      }
    } else if (itemType === "links") {
      const link = data.links.find(
        (l) =>
          `${l.area1Name}%${l.area2Name}` === selectedItemId ||
          `${l.area2Name}%${l.area1Name}` === selectedItemId,
      );

      if (!link) {
        return [];
      }

      link.variables.forEach((variable) => {
        options.push({ variable });
      });
    }

    return options;
  }, [variablesMetadata, mcMode, dataType, itemType, selectedItemId]);

  const selectedOption = variableOptions.find((opt) => opt.variable === selectedVariable) || null;

  return (
    <Autocomplete
      size="small"
      options={variableOptions}
      getOptionLabel={(option) => option.variable}
      value={selectedOption}
      onChange={(_event, newValue) => {
        onVariableSelect(newValue?.variable || "");
      }}
      disabled={disabled || variableOptions.length === 0}
      renderInput={(params) => (
        <StringFE
          {...params}
          label={t("study.results.variable")}
          margin="dense"
          sx={{ minWidth: 160 }}
        />
      )}
      noOptionsText={t("study.results.noVariables")}
    />
  );
}

export default VariableSelector;
