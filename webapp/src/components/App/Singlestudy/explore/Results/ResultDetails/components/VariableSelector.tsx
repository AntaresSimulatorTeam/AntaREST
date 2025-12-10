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

/**
 * Variable Selector Component for Variable-per-Variable Views
 *
 * This component allows users to select a variable from the list of available variables
 * for a given item (area or link) in the variable-per-variable mode.
 *
 * IMPORTANT: Variable-per-variable views always use mcInd (Monte Carlo Individual) data.
 * Although the API returns both mcInd and mcAll in the response, we exclusively use mcInd
 * because:
 * - mcInd contains non-aggregated, year-by-year individual simulation data
 * - This allows users to view all years for a specific variable in a consolidated table
 * - mcAll contains pre-aggregated statistics (sum, std, etc.) which doesn't benefit from
 *   variable-by-variable breakdown since it's already synthesized
 *
 * The mcAll data is used elsewhere (e.g., Synthesis view) but never in variable-per-variable mode.
 */

import { Autocomplete } from "@mui/material";
import { useEffect, useMemo } from "react";
import { useTranslation } from "react-i18next";
import StringFE from "@/components/common/fieldEditors/StringFE";
import type { VariablesListDTO } from "@/services/api/studies/outputs/variableViews/types";
import {
  getFirstVariableForItem,
  getVariables,
  getClusterVariables,
  type DataType,
  type OutputItemType,
} from "../utils";

interface VariableSelectorProps {
  variablesMetadata: VariablesListDTO | null;
  dataType: DataType;
  itemType: OutputItemType;
  selectedItemId: string;
  selectedVariable: string;
  onVariableSelect: (variable: string) => void;
  disabled?: boolean;
  selectedClusterId?: string;
}

function VariableSelector({
  variablesMetadata,
  dataType,
  itemType,
  selectedItemId,
  selectedVariable,
  onVariableSelect,
  disabled,
  selectedClusterId,
}: VariableSelectorProps) {
  const { t } = useTranslation();

  const variableOptions = useMemo(() => {
    if (!variablesMetadata || !selectedItemId) {
      return [];
    }

    // For cluster data types, get variables from the specific cluster
    const isClusterDataType = ["details", "details-res", "details-STstorage"].includes(dataType);

    if (isClusterDataType && selectedClusterId && itemType === "areas") {
      return getClusterVariables(variablesMetadata, selectedItemId, dataType, selectedClusterId);
    }

    return getVariables(variablesMetadata, itemType, selectedItemId, dataType);
  }, [variablesMetadata, dataType, itemType, selectedItemId, selectedClusterId]);

  const isVariableValid = variableOptions.includes(selectedVariable);

  // Auto-select first variable when switching item types or when no valid variable is selected
  useEffect(() => {
    if (!isVariableValid && variablesMetadata && selectedItemId) {
      const firstVariable = getFirstVariableForItem(variablesMetadata, itemType, selectedItemId);

      if (firstVariable) {
        onVariableSelect(firstVariable);
      }
    }
  }, [isVariableValid, variablesMetadata, selectedItemId, itemType, onVariableSelect]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Autocomplete
      size="extra-small"
      options={variableOptions}
      value={isVariableValid ? selectedVariable : null}
      onChange={(_event, newValue) => {
        onVariableSelect(newValue || "");
      }}
      disabled={disabled || variableOptions.length === 0}
      renderInput={(params) => (
        <StringFE
          {...params}
          label={t("study.results.variable")}
          margin="dense"
          sx={{ minWidth: 160 }}
          size="extra-small"
        />
      )}
      noOptionsText={t("study.results.noVariables")}
    />
  );
}

export default VariableSelector;
