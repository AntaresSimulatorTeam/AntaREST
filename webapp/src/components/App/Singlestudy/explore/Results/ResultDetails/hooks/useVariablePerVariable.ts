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
 * Hook: useVariablePerVariable
 *
 * Manages the state and operations for the variable-per-variable view mode.
 * This hook handles:
 * - Fetching the list of available variables from the API
 * - Managing variable selection state
 * - Fetching variable view data (consolidated year-by-year matrix)
 * - Materializing variable views when they haven't been generated yet
 * - Tracking materialization progress via WebSocket
 *
 * IMPORTANT - DATA SOURCE:
 * The variables list API endpoint (/v1/studies/{uuid}/output/{output_id}/variables-list)
 * returns both mcInd and mcAll data structures in a single response:
 *
 * Response structure:
 * {
 *   "mcInd": { areas: [...], links: [...] },  // Year-by-year individual simulation data
 *   "mcAll": { areas: [...], links: [...] }   // Pre-aggregated statistical data
 * }
 *
 * This hook and all variable-per-variable components EXCLUSIVELY use mcInd because:
 *
 * 1. mcInd (Monte Carlo Individual):
 *    - Contains non-aggregated, year-by-year data for each Monte Carlo simulation run
 *    - Essential for variable-per-variable views that show all years in a consolidated table
 *    - Enables users to analyze detailed simulation results without navigating 1000+ matrices
 *
 * 2. mcAll (Monte Carlo Aggregated):
 *    - Contains pre-aggregated statistics (sum, standard deviation, etc.)
 *    - Already synthesized, so no benefit from variable-by-variable breakdown
 *    - Used elsewhere in the application (e.g., Synthesis view with single matrix)
 *
 * The API design decision to return both in a single endpoint was made for practical reasons
 * (splitting into /mc-all and /mc-ind endpoints was deemed impractical), but the front-end
 * primarily consumes mcInd for variable-per-variable features.
 *
 * Note: The variable lists can differ between mcInd and mcAll for the same area/link.
 */

import { enqueueSnackbar } from "notistack";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import usePromise from "@/hooks/usePromise";
import { useTaskMonitor } from "@/hooks/useTaskMonitor";
import {
  getVariablesList,
  getVariableViewData,
  materializeVariableView,
} from "@/services/api/studies/outputs/variableViews";
import type { VariableViewParams } from "@/services/api/studies/outputs/variableViews/types";
import { WsChannel } from "@/services/webSocket/constants";
import { unsubscribeWsChannels } from "@/services/webSocket/ws";
import type { Area, LinkElement } from "@/types/types";
import type { OutputItemType, Timestep } from "../utils";

interface UseVariablePerVariableProps {
  studyId: string;
  outputId: string | undefined;
  isEnabled: boolean;
  itemType: OutputItemType;
  timestep: Timestep;
  selectedItemId: string;
  selectedItem: (Area & { id: string }) | LinkElement | undefined;
  dataType: string;
  selectedClusterId: string;
}

export function useVariablePerVariable({
  studyId,
  outputId,
  isEnabled,
  itemType,
  timestep,
  selectedItemId,
  selectedItem,
  dataType,
  selectedClusterId,
}: UseVariablePerVariableProps) {
  const { t } = useTranslation();
  const [selectedVariable, setSelectedVariable] = useState("");
  const [isMaterializing, setIsMaterializing] = useState(false);
  const [materializationTaskId, setMaterializationTaskId] = useState<string | null>(null);

  // Track which view was materialized to only reload if user is still on that view
  // If user navigates away during materialization, this ref is cleared to null
  const materializationParamsRef = useRef<{
    variable: string;
    itemId: string;
    itemType: OutputItemType;
    timestep: Timestep;
  } | null>(null);

  const { data: variablesMetadata } = usePromise(
    () => {
      if (outputId && isEnabled) {
        return getVariablesList(studyId, outputId);
      }

      return Promise.resolve(null);
    },
    { deps: [studyId, outputId, isEnabled] },
  );

  // TODO: Refactor variables data retrieval logic
  const variableViewDataRes = usePromise(
    async () => {
      if (!outputId || !selectedVariable || !selectedItemId || !selectedItem) {
        return null;
      }

      let params: VariableViewParams;

      if (itemType === "areas") {
        // Check if we're dealing with cluster data
        if (dataType === "details" && selectedClusterId) {
          params = {
            type: "thermal",
            variableName: selectedVariable,
            frequency: timestep,
            areaId: selectedItemId,
            clusterId: selectedClusterId,
          };
        } else if (dataType === "details-res" && selectedClusterId) {
          params = {
            type: "renewable",
            variableName: selectedVariable,
            frequency: timestep,
            areaId: selectedItemId,
            clusterId: selectedClusterId,
          };
        } else if (dataType === "details-STstorage" && selectedClusterId) {
          params = {
            type: "st_storage",
            variableName: selectedVariable,
            frequency: timestep,
            areaId: selectedItemId,
            clusterId: selectedClusterId,
          };
        } else {
          params = {
            type: "area",
            variableName: selectedVariable,
            frequency: timestep,
            areaId: selectedItemId,
          };
        }
      } else {
        params = {
          type: "link",
          variableName: selectedVariable,
          frequency: timestep,
          areaFromId: (selectedItem as LinkElement).area1,
          areaToId: (selectedItem as LinkElement).area2,
        };
      }

      const data = await getVariableViewData(studyId, outputId, params);
      return data;
    },
    {
      deps: [
        studyId,
        outputId,
        selectedVariable,
        selectedItemId,
        itemType,
        timestep,
        dataType,
        selectedClusterId,
      ],
    },
  );

  useEffect(() => {
    if (!isEnabled) {
      setSelectedVariable("");
      setIsMaterializing(false);
      setMaterializationTaskId(null);
    }
  }, [isEnabled]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: materializationTaskId is intentionally excluded to avoid infinite loop when unsubscribing
  useEffect(() => {
    setIsMaterializing(false);

    if (materializationTaskId) {
      unsubscribeWsChannels([WsChannel.Task + materializationTaskId]);
      setMaterializationTaskId(null);
    }

    // When user navigates to a different variable or item, cancel ongoing materialization
    // and clear the materialization params ref so we don't reload the wrong view
    materializationParamsRef.current = null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedVariable, selectedItemId]);

  const handleMaterializeVariable = async () => {
    if (!outputId || !selectedVariable || !selectedItemId || !selectedItem) {
      return;
    }

    try {
      setIsMaterializing(true);

      let params: VariableViewParams;

      if (itemType === "areas") {
        // Check if we're dealing with cluster data
        if (dataType === "details" && selectedClusterId) {
          params = {
            type: "thermal",
            variableName: selectedVariable,
            frequency: timestep,
            areaId: selectedItemId,
            clusterId: selectedClusterId,
          };
        } else if (dataType === "details-res" && selectedClusterId) {
          params = {
            type: "renewable",
            variableName: selectedVariable,
            frequency: timestep,
            areaId: selectedItemId,
            clusterId: selectedClusterId,
          };
        } else if (dataType === "details-STstorage" && selectedClusterId) {
          params = {
            type: "st_storage",
            variableName: selectedVariable,
            frequency: timestep,
            areaId: selectedItemId,
            clusterId: selectedClusterId,
          };
        } else {
          params = {
            type: "area",
            variableName: selectedVariable,
            frequency: timestep,
            areaId: selectedItemId,
          };
        }
      } else {
        params = {
          type: "link",
          variableName: selectedVariable,
          frequency: timestep,
          areaFromId: (selectedItem as LinkElement).area1,
          areaToId: (selectedItem as LinkElement).area2,
        };
      }

      const taskId = await materializeVariableView(studyId, outputId, params);
      setMaterializationTaskId(taskId);

      // Store the current view params to check later if user is still on this view
      materializationParamsRef.current = {
        variable: selectedVariable,
        itemId: selectedItemId,
        itemType,
        timestep,
      };
    } catch {
      // TODO use error snackbar
      enqueueSnackbar(t("study.results.materializationStartFailed"), { variant: "error" });
      setIsMaterializing(false);
    }
  };

  useTaskMonitor({
    taskId: materializationTaskId,
    onComplete: () => {
      setIsMaterializing(false);
      setMaterializationTaskId(null);

      // Only reload if user is still on the view that was materialized
      // (if user navigated away, the ref was cleared to null)
      if (materializationParamsRef.current) {
        variableViewDataRes.reload();
      }

      materializationParamsRef.current = null;
    },
    onFailed: useCallback(
      (message: string) => {
        setIsMaterializing(false);
        setMaterializationTaskId(null);
        // TODO use error snackbar
        enqueueSnackbar(message || t("study.results.materializationFailed"), {
          variant: "error",
        });
      },
      [t],
    ),
    // TODO add deps array + add in eslint config
  });

  return {
    variablesMetadata,
    selectedVariable,
    setSelectedVariable,
    isMaterializing,
    handleMaterializeVariable,
    variableViewDataRes,
  };
}
