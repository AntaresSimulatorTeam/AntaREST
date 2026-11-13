/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import { streamStudyCheck } from "@/services/api/assistant";
import type { CheckLanguage } from "@/services/api/assistant/types";
import { toError } from "@/utils/fnUtils";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  INITIAL_CHECK_STATE,
  reduceCheckEvent,
  RUNNING_CHECK_STATE,
  type StudyCheckState,
} from "./utils";

/**
 * Runs the check of a study by the AI assistant and follows its progress.
 *
 * The state lives as long as the component: the result stays available after the panel showing
 * it is closed. A running check is stopped when the component unmounts.
 *
 * @param studyId - The study to check.
 * @param language - Language of the analysis written by the assistant.
 * @returns The state of the check, with `start` and `cancel`.
 */
function useStudyCheck(studyId: string, language: CheckLanguage) {
  const [state, setState] = useState<StudyCheckState>(INITIAL_CHECK_STATE);
  const controllerRef = useRef<AbortController | null>(null);

  const cancel = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setState((prev) => (prev.status === "running" ? INITIAL_CHECK_STATE : prev));
  }, []);

  const start = useCallback(async () => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setState(RUNNING_CHECK_STATE);

    try {
      await streamStudyCheck({
        studyId,
        language,
        signal: controller.signal,
        onEvent: (event) => {
          // Events of a cancelled or replaced check are ignored
          if (controllerRef.current === controller) {
            setState((prev) => reduceCheckEvent(prev, event));
          }
        },
      });

      if (controllerRef.current === controller) {
        // The stream ended without a final event
        setState((prev) => (prev.status === "running" ? { ...prev, status: "error" } : prev));
      }
    } catch (err) {
      if (controllerRef.current === controller) {
        setState((prev) => ({ ...prev, status: "error", error: toError(err).message }));
      }
    }
  }, [studyId, language]);

  useEffect(() => {
    return () => controllerRef.current?.abort();
  }, []);

  return { state, start, cancel };
}

export default useStudyCheck;
