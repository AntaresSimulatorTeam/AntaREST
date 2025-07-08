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

import useStudySynthesis from "@/redux/hooks/useStudySynthesis";
import { getStudyOutput } from "@/redux/selectors";
import { getStudyOutputById, getStudyData } from "@/services/api/study";
import type { StudyOutput } from "@/types/types";
import { MAX_YEAR } from "../ResultDetails/utils";
import usePromise from "@/hooks/usePromise";

interface UseStudyOutputOptions {
  studyId: string;
  outputId: string | undefined;
}

// Partial output type for cases where we don't have all the data
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
  settings?: Partial<StudyOutput["settings"]> | Record<string, unknown>;
  completionDate?: string;
  status?: string;
  archived?: boolean;
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
export default function useStudyOutput({ studyId, outputId }: UseStudyOutputOptions): {
  data: PartialStudyOutput | undefined;
  isLoading: boolean;
  error: unknown;
} {
  // Try to get output from Redux store
  const { data: outputFromStore } = useStudySynthesis({
    studyId,
    selector: (state, id) => (outputId ? getStudyOutput(state, id, outputId) : undefined),
  });

  // Fetch output metadata if not in store (e.g. for some variants where output might not be in the store)
  const {
    data: fetchedOutput,
    isLoading,
    error,
  } = usePromise<PartialStudyOutput | undefined>(
    async () => {
      if (outputFromStore) {
        console.log("from store", outputFromStore);
        return outputFromStore;
      }

      if (!outputId) {
        return undefined;
      }

      const output = await getStudyOutputById(studyId, outputId);

      console.log("output", output);

      if (output) {
        return {
          id: outputId,
          ...output,
        };
      }

      // If no output info, try to get output settings
      const outputSettings = await getStudyData(
        studyId,
        `output/${outputId}/about-the-study/parameters`,
      );

      console.log("outputSettings", outputSettings);

      if (outputSettings) {
        // Construct output object from settings
        return {
          id: outputId,
          name: outputId,
          mode: outputSettings.general?.mode || "economy",
          nbyears: outputSettings.general?.nbyears || MAX_YEAR,
          synthesis: outputSettings.output?.synthesis ?? true,
          date: new Date().toISOString(),
          by_year: outputSettings.general?.["year-by-year"] ?? true,
          error: false,
          settings: outputSettings,
        };
      }
    },
    {
      deps: [studyId, outputId, outputFromStore],
    },
  );

  return {
    data: outputFromStore || fetchedOutput,
    isLoading,
    error,
  };
}
