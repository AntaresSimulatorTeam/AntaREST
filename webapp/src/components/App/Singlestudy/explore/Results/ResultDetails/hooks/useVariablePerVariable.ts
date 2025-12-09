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
 * Manages the state and operations for the variable-per-variable view mode.
 *
 * The variables list API endpoint (/v1/studies/{uuid}/output/{output_id}/variables-list)
 * returns both mcInd and mcAll data structures in a single response:
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
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import usePromise from "@/hooks/usePromise";
import { useTaskMonitor } from "@/hooks/useTaskMonitor";
import {
  getVariablesList,
  getVariableViewData,
  materializeVariableView,
} from "@/services/api/studies/outputs/variableViews";
import type { Area, LinkElement } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import { buildVariableViewParams, type Frequency, type OutputItemType } from "../utils";

interface UseVariablePerVariableProps {
  studyId: string;
  outputId: string | undefined;
  isEnabled: boolean;
  itemType: OutputItemType;
  frequency: Frequency;
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
  frequency,
  selectedItemId,
  selectedItem,
  dataType,
  selectedClusterId,
}: UseVariablePerVariableProps) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [selectedVariable, setSelectedVariable] = useState("");
  const [isMaterializing, setIsMaterializing] = useState(false);
  const [materializationTaskId, setMaterializationTaskId] = useState<string | null>(null);

  // Track which view was materialized to only reload if user is still on that view
  // If user navigates away during materialization, this ref is cleared to null
  const materializationParamsRef = useRef<{
    variable: string;
    itemId: string;
    itemType: OutputItemType;
    frequency: Frequency;
  } | null>(null);

  const { data: variablesMetadata } = usePromise(
    () => {
      if (outputId && isEnabled) {
        return getVariablesList({ studyId, outputId });
      }

      return Promise.resolve(null);
    },
    { deps: [studyId, outputId, isEnabled] },
  );

  const variableViewDataRes = usePromise(
    async () => {
      if (!outputId || !selectedVariable || !selectedItemId || !selectedItem) {
        return null;
      }

      const params = buildVariableViewParams(
        itemType,
        dataType,
        selectedClusterId,
        selectedItemId,
        selectedItem,
        selectedVariable,
        frequency,
      );

      const data = await getVariableViewData({ studyId, outputId, params });
      return data;
    },
    {
      deps: [
        studyId,
        outputId,
        selectedVariable,
        selectedItemId,
        itemType,
        frequency,
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

  // biome-ignore lint/correctness/useExhaustiveDependencies: Effect intentionally runs when selectedVariable or selectedItemId changes to cancel ongoing materialization
  useEffect(() => {
    // When user navigates to a different variable or item
    // clear the materialization ref so we don't reload the wrong view
    setIsMaterializing(false);
    setMaterializationTaskId(null);
    materializationParamsRef.current = null;
  }, [selectedVariable, selectedItemId]);

  const handleMaterializeVariable = async () => {
    if (!outputId || !selectedVariable || !selectedItemId || !selectedItem) {
      return;
    }

    try {
      setIsMaterializing(true);

      const params = buildVariableViewParams(
        itemType,
        dataType,
        selectedClusterId,
        selectedItemId,
        selectedItem,
        selectedVariable,
        frequency,
      );

      const taskId = await materializeVariableView({ studyId, outputId, params });

      setMaterializationTaskId(taskId);

      // Store the current view params to check later if user is still on this view
      materializationParamsRef.current = {
        variable: selectedVariable,
        itemId: selectedItemId,
        itemType,
        frequency,
      };
    } catch (error) {
      enqueueErrorSnackbar(t("study.results.materializationStartFailed"), toError(error));
      setIsMaterializing(false);
    }
  };

  useTaskMonitor({
    taskId: materializationTaskId,
    onComplete: useCallback(() => {
      setIsMaterializing(false);
      setMaterializationTaskId(null);

      // Only fetch data if user is still on the view that was materialized
      if (materializationParamsRef.current) {
        variableViewDataRes.reload();
      }

      materializationParamsRef.current = null;
    }, [variableViewDataRes]),
    onFailed: useCallback(
      (message: string) => {
        setIsMaterializing(false);
        setMaterializationTaskId(null);
        enqueueErrorSnackbar(t("study.results.materializationFailed"), new Error(message));
        materializationParamsRef.current = null;
      },
      [enqueueErrorSnackbar, t],
    ),
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
