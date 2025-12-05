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
import type {
  AreaVariablesDTO,
  RenewableClusterVariablesDTO,
  ShortTermStorageVariablesDTO,
  ThermalClusterVariablesDTO,
  VariablesListDTO,
} from "@/services/api/studies/outputs/variableViews/types";
import { getFirstVariableForItem, type DataType, type OutputItemType } from "../utils";

interface VariableSelectorProps {
  variablesMetadata: VariablesListDTO | null;
  dataType: DataType;
  itemType: OutputItemType;
  selectedItemId: string;
  selectedVariable: string;
  onVariableSelect: (variable: string) => void;
  disabled?: boolean;
}

/**
 * Extracts variables from an area based on the data type
 *
 * @param area - The area containing variables and clusters
 * @param dataType - The type of data to extract (values, details, details-res, details-STstorage)
 * @returns Array of variable names
 */
function getAreaVariables(area: AreaVariablesDTO, dataType: DataType): string[] {
  switch (dataType) {
    case "values":
      return area.variables;

    case "details":
      return (
        area.thermalClusters?.flatMap((cluster: ThermalClusterVariablesDTO) => cluster.variables) ||
        []
      );

    case "details-res":
      return (
        area.renewableClusters?.flatMap(
          (cluster: RenewableClusterVariablesDTO) => cluster.variables,
        ) || []
      );

    case "details-STstorage":
      return (
        area.shortTermStorages?.flatMap(
          (storage: ShortTermStorageVariablesDTO) => storage.variables,
        ) || []
      );

    default:
      return [];
  }
}

/**
 * Checks if a link matches the selected ID (bidirectional match)
 *
 * @param area1 - First area name
 * @param area2 - Second area name
 * @param selectedId - The selected link ID to match against
 * @returns True if the link matches in either direction
 */
function isLinkMatch(area1: string, area2: string, selectedId: string): boolean {
  const linkId1 = `${area1}%${area2}`;
  const linkId2 = `${area2}%${area1}`;
  return linkId1 === selectedId || linkId2 === selectedId;
}

/**
 * Extracts variables based on item type (areas or links)
 *
 * @param variablesMetadata - The metadata containing all variables information
 * @param itemType - The type of item (areas or links)
 * @param selectedItemId - The ID of the selected item
 * @param dataType - The type of data to extract
 * @returns Array of variable names
 */
function getVariables(
  variablesMetadata: VariablesListDTO,
  itemType: OutputItemType,
  selectedItemId: string,
  dataType: DataType,
): string[] {
  const data = variablesMetadata.mcInd;

  if (itemType === "areas") {
    const area = data.areas.find((a) => a.name === selectedItemId);
    return area ? getAreaVariables(area, dataType) : [];
  }

  if (itemType === "links") {
    const link = data.links.find((link) =>
      isLinkMatch(link.area1Name, link.area2Name, selectedItemId),
    );
    return link?.variables || [];
  }

  return [];
}

function VariableSelector({
  variablesMetadata,
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

    return getVariables(variablesMetadata, itemType, selectedItemId, dataType);
  }, [variablesMetadata, dataType, itemType, selectedItemId]);

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
      size="small"
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
        />
      )}
      noOptionsText={t("study.results.noVariables")}
    />
  );
}

export default VariableSelector;
