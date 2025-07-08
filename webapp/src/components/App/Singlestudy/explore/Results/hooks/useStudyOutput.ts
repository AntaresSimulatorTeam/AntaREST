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

/* eslint-disable no-console */

import { useMemo } from "react";
import useStudySynthesis from "@/redux/hooks/useStudySynthesis";
import { getStudyOutput } from "@/redux/selectors";
import { getStudyData, getStudyOutputById } from "@/services/api/study";

import { MAX_YEAR } from "../ResultDetails/utils";
import usePromise from "@/hooks/usePromise";

interface UseStudyOutputOptions {
  studyId: string;
  outputId: string | undefined;
}

interface PartialStudyOutput {
  id: string;
  name: string;
  mode?: string;
  nbyears?: number;
  synthesis?: boolean;
  date?: string;
  by_year?: boolean;
  error?: boolean;
  type?: string;
  settings?: Record<string, unknown>;
  completionDate?: string;
  status?: string;
  archived?: boolean;
}

interface UseStudyOutputReturn {
  data: PartialStudyOutput | undefined;
  isLoading: boolean;
  error: unknown;
}

/**
 * Hook to fetch study output metadata.
 * First tries to get it from Redux store, then falls back to API calls.
 * Handles variants where output might not be in the store.
 *
 * @param options - The options object
 * @param options.studyId - The study ID
 * @param options.outputId - The output ID (optional)
 * @returns Object containing the output data, loading state, and error
 */
export default function useStudyOutput({
  studyId,
  outputId,
}: UseStudyOutputOptions): UseStudyOutputReturn {
  // Try to get output from Redux store
  const { data: outputFromStore } = useStudySynthesis({
    studyId,
    selector: (state, id) => (outputId ? getStudyOutput(state, id, outputId) : undefined),
  });

  // Check if we have the output in store to avoid unnecessary API calls
  const hasOutputInStore = useMemo(() => !!outputFromStore, [outputFromStore]);

  // Fetch output metadata if not in store
  const {
    data: fetchedOutput,
    isLoading,
    error,
  } = usePromise<PartialStudyOutput | undefined>(
    async () => {
      // Skip API call if we already have the data in store
      if (hasOutputInStore) {
        console.log("[useStudyOutput] Output found in store:", outputId);
        return undefined;
      }

      if (!outputId) {
        return undefined;
      }

      // BUG: For variants, after a generation job is initiated, we must await the job
      // completion to display results. However, the WebSocket listener that should notify
      // us of job completion never gets triggered for this particular case. This causes
      // variant outputs to remain outdated/unavailable until the app is manually refreshed.
      // As a workaround, we attempt to fetch the output directly.
      //
      // TODO: The API should ensure that the WebSocket listener is properly set up to notify
      // us of job completion.

      console.log("[useStudyOutput] Fetching output from API:", outputId);

      const foundOutput = await getStudyOutputById(studyId, outputId);

      if (foundOutput) {
        console.log("[useStudyOutput] Found output from API by ID:", {
          id: outputId,
          output: foundOutput,
        });

        return {
          id: outputId,
          ...foundOutput,
        };
      }

      console.log("[useStudyOutput] Output not in list, trying to get settings:", outputId);

      const outputSettings = await getStudyData(
        studyId,
        `output/${outputId}/about-the-study/parameters`,
      );

      // This case should never happen, but just in case
      // we use a hard-coded default value to be able to display the output
      if (!outputSettings) {
        console.log("[useStudyOutput] Got output settings:", outputSettings);
        return {
          id: outputId,
          name: outputId,
          mode: outputSettings.general?.mode || "economy",
          nbyears: outputSettings.general?.nbyears || MAX_YEAR,
          synthesis: outputSettings.output?.synthesis ?? true,
          date: new Date().toISOString(),
          by_year: outputSettings.general?.["year-by-year"] ?? true,
          error: false,
          type: "economy",
          settings: outputSettings,
          completionDate: new Date().toISOString(),
          status: "completed",
          archived: false,
        };
      }

      // Return undefined to let the component handle the missing output
      console.log("[useStudyOutput] Output not found, returning undefined");
      return undefined;
    },
    {
      // Only depend on studyId, outputId, and whether we have the data in store
      // This prevents infinite loops caused by outputFromStore reference changes
      deps: [studyId, outputId, hasOutputInStore],
    },
  );

  const data = useMemo(() => {
    if (outputFromStore) {
      return outputFromStore;
    }

    return fetchedOutput;
  }, [outputFromStore, fetchedOutput]);

  return {
    data,
    isLoading: !hasOutputInStore && isLoading,
    error: !hasOutputInStore ? error : undefined,
  };
}
