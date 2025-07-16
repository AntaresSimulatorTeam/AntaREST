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

import usePromise from "@/hooks/usePromise";
import useStudySynthesis from "@/redux/hooks/useStudySynthesis";
import { getStudyOutput } from "@/redux/selectors";
import { getStudyOutputById } from "@/services/api/study";

interface UseStudyOutputOptions {
  studyId: string;
  outputId: string | undefined;
}

export interface PartialStudyOutput {
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
  const { data: outputFromStore } = useStudySynthesis({
    studyId,
    selector: (state, id) => (outputId ? getStudyOutput(state, id, outputId) : undefined),
  });

  const {
    data: fetchedOutput,
    isLoading,
    error,
  } = usePromise<PartialStudyOutput | undefined>(
    async () => {
      if (outputFromStore) {
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

      const foundOutput = await getStudyOutputById(studyId, outputId);

      if (foundOutput) {
        return {
          ...foundOutput,
          id: outputId,
        };
      }

      return undefined;
    },
    {
      // Only depend on studyId, outputId, and whether we have data in store.
      // !!outputFromStore to avoid re-running when the object reference changes but the value remains truthy/falsy.
      deps: [studyId, outputId, !!outputFromStore],
    },
  );

  return {
    data: outputFromStore || fetchedOutput,
    isLoading: !outputFromStore && isLoading,
    error: !outputFromStore ? error : undefined,
  };
}
