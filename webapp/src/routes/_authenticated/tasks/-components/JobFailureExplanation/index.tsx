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

import { assistantQueries } from "@/queries/assistant/queries";
import { streamJobExplanation } from "@/services/api/assistant";
import type { JobFailureCause } from "@/services/api/assistant/types";
import { toError } from "@/utils/fnUtils";
import ReplayIcon from "@mui/icons-material/Replay";
import TroubleshootIcon from "@mui/icons-material/Troubleshoot";
import {
  Alert,
  AlertTitle,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  LinearProgress,
  Paper,
  Skeleton,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import Markdown from "react-markdown";
import {
  INITIAL_EXPLANATION_STATE,
  reduceExplanationEvent,
  RUNNING_EXPLANATION_STATE,
  type JobExplanationState,
} from "./utils";

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
  jobId: string;
}

// Button shown on a failed simulation: asks the AI assistant why it failed, and shows the
// probable causes found in the logs, then the explanation and what to do.
// Nothing is rendered if the server has no assistant.
function JobFailureExplanation({ jobId }: Props) {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<JobExplanationState>(INITIAL_EXPLANATION_STATE);
  const controllerRef = useRef<AbortController | null>(null);
  const { data: assistant } = useQuery(assistantQueries.status());
  const language = i18n.language?.startsWith("fr") ? "fr" : "en";

  const start = useCallback(async () => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setState(RUNNING_EXPLANATION_STATE);

    try {
      await streamJobExplanation({
        jobId,
        language,
        signal: controller.signal,
        onEvent: (event) => {
          // Events of a cancelled or replaced request are ignored
          if (controllerRef.current === controller) {
            setState((prev) => reduceExplanationEvent(prev, event));
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
  }, [jobId, language]);

  useEffect(() => {
    return () => controllerRef.current?.abort();
  }, []);

  if (!assistant?.available) {
    return null;
  }

  const { status, phase, diagnosis, diagnosisError, answer, error, extraTools } = state;
  const isRunning = status === "running";

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleOpen = () => {
    setOpen(true);

    if (status === "idle") {
      start();
    }
  };

  const handleClose = () => {
    setOpen(false);

    if (isRunning) {
      controllerRef.current?.abort();
      controllerRef.current = null;
      setState(INITIAL_EXPLANATION_STATE);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Tooltip title={t("tasks.explain.button")}>
        <IconButton onClick={handleOpen} size="small" aria-label={t("tasks.explain.button")}>
          <TroubleshootIcon />
        </IconButton>
      </Tooltip>
      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>{t("tasks.explain.title")}</DialogTitle>
        <DialogContent dividers>
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
        </DialogContent>
        <DialogActions>
          {!isRunning && status !== "idle" && (
            <Button startIcon={<ReplayIcon />} onClick={start}>
              {t("tasks.explain.restart")}
            </Button>
          )}
          <Button onClick={handleClose} variant="contained">
            {t(isRunning ? "global.cancel" : "global.close")}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export default JobFailureExplanation;
