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
import { subscribeWsChannels, unsubscribeWsChannels } from "@/services/webSocket/ws";
import {
  getFirstVariableForItem,
  type MonteCarloMode,
  type OutputItemType,
  type Timestep,
} from "../utils";

interface UseVariablePerVariableProps {
  studyId: string;
  outputId: string | undefined;
  isEnabled: boolean;
  mcMode: MonteCarloMode;
  itemType: OutputItemType;
  timestep: Timestep;
  selectedItemId: string;
}

export function useVariablePerVariable({
  studyId,
  outputId,
  isEnabled,
  mcMode,
  itemType,
  timestep,
  selectedItemId,
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

  const variableViewDataRes = usePromise(
    async () => {
      if (!outputId || !selectedVariable || !selectedItemId) {
        return null;
      }

      const params: VariableViewParams = {
        type: itemType === "areas" ? "area" : "link",
        variableName: selectedVariable,
        frequency: timestep as VariableViewParams["frequency"],
        ...(itemType === "areas" ? { areaId: selectedItemId } : { linkId: selectedItemId }),
      } as VariableViewParams;

      const data = await getVariableViewData(studyId, outputId, params);
      return data;
    },
    {
      deps: [studyId, outputId, selectedVariable, selectedItemId, itemType, timestep],
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

  useEffect(() => {
    if (isEnabled && variablesMetadata && selectedItemId && !selectedVariable) {
      const firstVariable = getFirstVariableForItem(
        variablesMetadata,
        mcMode,
        itemType,
        selectedItemId,
      );

      if (firstVariable) {
        setSelectedVariable(firstVariable);
      }
    }
  }, [isEnabled, variablesMetadata, selectedItemId, selectedVariable, itemType, mcMode]);

  const handleMaterializeVariable = async () => {
    if (!outputId || !selectedVariable || !selectedItemId) {
      return;
    }

    try {
      setIsMaterializing(true);

      const params: VariableViewParams = {
        type: itemType === "areas" ? "area" : "link",
        variableName: selectedVariable,
        frequency: timestep as VariableViewParams["frequency"],
        ...(itemType === "areas" ? { areaId: selectedItemId } : { linkId: selectedItemId }),
      } as VariableViewParams;

      const taskId = await materializeVariableView(studyId, outputId, params);
      setMaterializationTaskId(taskId);

      // Store the current view params to check later if user is still on this view
      materializationParamsRef.current = {
        variable: selectedVariable,
        itemId: selectedItemId,
        itemType,
        timestep,
      };

      subscribeWsChannels([WsChannel.Task + taskId]);
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
        enqueueSnackbar(message || t("study.results.materializationFailed"), {
          variant: "error",
        });
      },
      [t],
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
