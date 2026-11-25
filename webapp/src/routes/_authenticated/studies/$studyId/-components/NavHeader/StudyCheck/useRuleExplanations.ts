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

import { streamFindingsExplanation } from "@/services/api/assistant";
import type { CheckLanguage } from "@/services/api/assistant/types";
import { toError } from "@/utils/fnUtils";
import { useEffect, useRef, useState } from "react";
import {
  INITIAL_REPORT_STATE,
  reduceReportEvent,
  type AssistantReportState,
  type RuleGroup,
} from "./utils";

function abortAll(controllers: Map<string, AbortController>) {
  for (const controller of controllers.values()) {
    controller.abort();
  }
}

/**
 * Explanations of the findings of a check by the AI assistant, one per rule, each asked for by
 * the user: the AI model is only called for the rules the user wants explained.
 *
 * The explanations live as long as the component: put the hook above what the user can close
 * (drawer), so that an explanation goes on and is kept when it is closed.
 *
 * @param studyId - Study which was checked.
 * @param language - Language of the explanations.
 * @returns The explanations by rule, with `explain` (which replaces a previous explanation of
 * the rule) and `reset`.
 */
function useRuleExplanations(studyId: string, language: CheckLanguage) {
  const [explanations, setExplanations] = useState<Record<string, AssistantReportState>>({});
  const controllersRef = useRef(new Map<string, AbortController>());

  useEffect(() => {
    const controllers = controllersRef.current;
    return () => abortAll(controllers);
  }, []);

  const explain = async ({ rule, findings }: RuleGroup) => {
    controllersRef.current.get(rule)?.abort();
    const controller = new AbortController();
    controllersRef.current.set(rule, controller);
    // Events of a replaced or forgotten explanation are ignored
    const update = (next: (prev: AssistantReportState) => AssistantReportState) => {
      if (controllersRef.current.get(rule) === controller) {
        setExplanations((prev) => ({ ...prev, [rule]: next(prev[rule] ?? INITIAL_REPORT_STATE) }));
      }
    };
    update(() => ({ ...INITIAL_REPORT_STATE, status: "running" }));

    try {
      await streamFindingsExplanation({
        studyId,
        language,
        findings,
        signal: controller.signal,
        onEvent: (event) => update((prev) => reduceReportEvent(prev, event)),
      });
      // The stream ended without a final event
      update((prev) => (prev.status === "running" ? { ...prev, status: "error" } : prev));
    } catch (err) {
      update((prev) => ({ ...prev, status: "error", error: toError(err).message }));
    }
  };

  const reset = () => {
    abortAll(controllersRef.current);
    controllersRef.current.clear();
    setExplanations({});
  };

  return { explanations, explain, reset };
}

export default useRuleExplanations;
