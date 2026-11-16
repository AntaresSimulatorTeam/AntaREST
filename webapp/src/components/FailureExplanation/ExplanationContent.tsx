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

import type { JobFailureCause } from "@/services/api/assistant/types";
import {
  Alert,
  AlertTitle,
  Box,
  Chip,
  LinearProgress,
  Paper,
  Skeleton,
  Stack,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import Markdown from "react-markdown";
import type { JobExplanationState } from "./utils";

const CONFIDENCE_COLORS = { high: "error", medium: "warning", low: "default" } as const;

const LOG_SX = {
  m: 0,
  p: 1,
  fontFamily: "monospace",
  fontSize: "0.8em",
  whiteSpace: "pre-wrap",
  overflowWrap: "anywhere",
  maxHeight: 180,
  overflow: "auto",
  bgcolor: "action.hover",
  borderRadius: 1,
} as const;

interface CauseProps {
  cause: JobFailureCause;
  // The texts of the rules are in English: shown only when the assistant could not explain
  showDetails: boolean;
}

function Cause({ cause, showDetails }: CauseProps) {
  const { t } = useTranslation();

  return (
    <Paper variant="outlined" sx={{ p: 1.5 }}>
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", mb: 1 }}>
        <Typography variant="body2" sx={{ fontWeight: "bold" }}>
          {t(`tasks.explain.cause.${cause.code}`, { defaultValue: cause.title })}
        </Typography>
        <Chip
          label={t(`tasks.explain.confidence.${cause.confidence}`)}
          color={CONFIDENCE_COLORS[cause.confidence]}
          variant="outlined"
          size="small"
        />
      </Stack>
      {showDetails && (
        <Typography variant="body2" sx={{ mb: 1 }}>
          {cause.explanation} {cause.suggestion}
        </Typography>
      )}
      <Box component="pre" sx={LOG_SX}>
        {cause.evidence.join("\n")}
      </Box>
    </Paper>
  );
}

interface Props {
  state: JobExplanationState;
}

// Explanation of a failed simulation: progress, probable causes found by the rules in the logs,
// decisive log lines, then the explanation of the assistant. Shared by the explanation of a job
// (Tasks page) and of logs given by the user (study header).
function ExplanationContent({ state }: Props) {
  const { t } = useTranslation();
  const { status, phase, diagnosis, diagnosisError, answer, error, extraTools } = state;
  const isRunning = status === "running";

  return (
    <Stack direction="column" spacing={3}>
      {isRunning && (
        <Stack direction="column" spacing={1} role="status">
          <Typography variant="body2" sx={{ fontWeight: "bold" }}>
            {t(`tasks.explain.phase.${phase}`)}
          </Typography>
          <LinearProgress aria-label={t(`tasks.explain.phase.${phase}`)} />
        </Stack>
      )}

      {status === "error" && (
        <Alert severity="error">
          <AlertTitle>{t("tasks.explain.failed")}</AlertTitle>
          {error}
        </Alert>
      )}

      {diagnosisError !== undefined && (
        <Alert severity="warning">
          <AlertTitle>{t("tasks.explain.diagnosisFailed")}</AlertTitle>
          {diagnosisError}
        </Alert>
      )}

      {answer && (
        <Box component="section">
          <Typography variant="subtitle1" component="h3" sx={{ fontWeight: "bold" }}>
            {t("tasks.explain.explanation")}
          </Typography>
          <Box sx={{ typography: "body2", overflowWrap: "anywhere" }}>
            <Markdown>{answer}</Markdown>
          </Box>
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            {t("tasks.explain.aiDisclaimer")}
          </Typography>
        </Box>
      )}

      {isRunning && phase === "explaining" && (
        <Box component="section">
          <Typography variant="subtitle1" component="h3" sx={{ fontWeight: "bold" }}>
            {t("tasks.explain.explanation")}
          </Typography>
          <Typography variant="body2" sx={{ color: "text.secondary", my: 1 }}>
            {extraTools.length > 0
              ? t("tasks.explain.digging", { count: extraTools.length })
              : t("tasks.explain.writing")}
          </Typography>
          <Skeleton />
          <Skeleton />
          <Skeleton width="60%" />
        </Box>
      )}

      {diagnosis && (
        <Box component="section">
          <Typography variant="subtitle1" component="h3" sx={{ mb: 1, fontWeight: "bold" }}>
            {t("tasks.explain.causes")}
          </Typography>
          {diagnosis.causes.length > 0 ? (
            <Stack direction="column" spacing={1}>
              {diagnosis.causes.map((cause) => (
                <Cause key={cause.code} cause={cause} showDetails={status === "error"} />
              ))}
            </Stack>
          ) : (
            <Alert severity="info">{t("tasks.explain.noKnownCause")}</Alert>
          )}
        </Box>
      )}

      {diagnosis && diagnosis.errorLines.length > 0 && (
        <Box component="section">
          <Typography variant="subtitle1" component="h3" sx={{ mb: 1, fontWeight: "bold" }}>
            {t("tasks.explain.errorLines")}
          </Typography>
          <Box component="pre" sx={LOG_SX}>
            {diagnosis.errorLines.join("\n")}
          </Box>
        </Box>
      )}
    </Stack>
  );
}

export default ExplanationContent;
