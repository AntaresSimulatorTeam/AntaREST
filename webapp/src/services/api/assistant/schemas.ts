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

import { z } from "zod";

////////////////////////////////////////////////////////////////
// Stream Events
////////////////////////////////////////////////////////////////

export const assistantEventSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("tool_call"),
    name: z.string(),
    input: z.record(z.string(), z.unknown()),
  }),
  z.object({
    type: z.literal("tool_progress"),
    name: z.string(),
    progress: z.number(),
    total: z.number().nullish(),
    message: z.string().nullish(),
  }),
  z.object({
    type: z.literal("tool_result"),
    name: z.string(),
    is_error: z.boolean(),
    duration_s: z.number(),
    // What the tool returned to the assistant (JSON text for most tools)
    content: z.string().optional(),
  }),
  z.object({
    type: z.literal("text"),
    text: z.string(),
  }),
  z.object({
    type: z.literal("done"),
    answer: z.string(),
    model: z.string().optional(),
    stop_reason: z.string().optional(),
    // Opaque state of the conversation, to send back with the next message
    history: z.array(z.unknown()).optional(),
  }),
  z.object({
    type: z.literal("error"),
    message: z.string(),
  }),
]);

////////////////////////////////////////////////////////////////
// Result of the `check_study` tool
////////////////////////////////////////////////////////////////

export const checkFindingSchema = z.object({
  rule: z.string(),
  severity: z.enum(["error", "warning", "info"]),
  message: z.string(),
  // Only the first objects are listed, `count` is the total
  objects: z.array(z.string()),
  count: z.number(),
});

export const checkReportSchema = z
  .object({
    summary: z.object({
      error: z.number(),
      warning: z.number(),
      info: z.number(),
    }),
    findings: z.array(checkFindingSchema),
    rules_run: z.array(z.string()),
    rules_skipped: z.array(z.string()),
    notes: z.array(z.string()),
  })
  .transform((report) => ({
    summary: report.summary,
    findings: report.findings,
    notes: report.notes,
    rulesRun: report.rules_run,
    rulesSkipped: report.rules_skipped,
  }));

////////////////////////////////////////////////////////////////
// Result of the `diagnose_job` tool
////////////////////////////////////////////////////////////////

export const jobFailureCauseSchema = z.object({
  code: z.string(),
  confidence: z.enum(["high", "medium", "low"]),
  title: z.string(),
  explanation: z.string(),
  suggestion: z.string(),
  // Log lines or facts the cause relies on
  evidence: z.array(z.string()),
});

export const jobDiagnosisSchema = z
  .object({
    causes: z.array(jobFailureCauseSchema),
    error_lines: z.array(z.string()),
    last_lines: z.array(z.string()),
    notes: z.array(z.string()),
  })
  .transform((diagnosis) => ({
    causes: diagnosis.causes,
    notes: diagnosis.notes,
    errorLines: diagnosis.error_lines,
    lastLines: diagnosis.last_lines,
  }));
