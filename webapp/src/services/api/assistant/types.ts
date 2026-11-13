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

import type { z } from "zod";
import type { assistantEventSchema, checkFindingSchema, checkReportSchema } from "./schemas";

export interface AssistantStatusDTO {
  available: boolean;
  reason: string;
  provider: string;
  model: string;
  read_only: boolean;
}

export interface AssistantStatus {
  available: boolean;
  /** Why the assistant is not available. */
  reason: string;
  provider: string;
  model: string;
  readOnly: boolean;
}

/** An event of the assistant while it answers (one JSON line of the stream). */
export type AssistantEvent = z.infer<typeof assistantEventSchema>;

export type CheckSeverity = "error" | "warning" | "info";

/** A possible inconsistency found by a rule of `check_study`. */
export type CheckFinding = z.infer<typeof checkFindingSchema>;

/** Result of the `check_study` tool. */
export type CheckReport = z.infer<typeof checkReportSchema>;

export type CheckLanguage = "en" | "fr";

export interface StreamStudyCheckParams {
  studyId: string;
  language: CheckLanguage;
  signal: AbortSignal;
  onEvent: (event: AssistantEvent) => void;
}
