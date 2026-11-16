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

import ExplanationContent from "@/components/FailureExplanation/ExplanationContent";
import {
  INITIAL_EXPLANATION_STATE,
  reduceExplanationEvent,
  RUNNING_EXPLANATION_STATE,
  type JobExplanationState,
} from "@/components/FailureExplanation/utils";
import { assistantQueries } from "@/queries/assistant/queries";
import { streamLogsExplanation } from "@/services/api/assistant";
import { toError } from "@/utils/fnUtils";
import ReceiptLongOutlinedIcon from "@mui/icons-material/ReceiptLongOutlined";
import ReplayIcon from "@mui/icons-material/Replay";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

const PASTED_LOGS_FILE_NAME = "logs.txt";
// Limit of the server. The end of the logs holds the failure: the beginning is cut.
const MAX_LOGS_CHARS = 20_000_000;
const PREVIEW_LINES = 15;

interface LogFile {
  name: string;
  text: string;
  isCut: boolean;
}

const PREVIEW_SX = {
  m: 0,
  p: 1,
  fontFamily: "monospace",
  fontSize: "0.8em",
  whiteSpace: "pre-wrap",
  overflowWrap: "anywhere",
  maxHeight: 220,
  overflow: "auto",
  bgcolor: "action.hover",
  borderRadius: 1,
} as const;

function readFileText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(typeof reader.result === "string" ? reader.result : "");
    reader.onerror = () => reject(reader.error ?? new Error(file.name));
    reader.readAsText(file);
  });
}

interface Props {
  studyId: string;
}

// Button of the study header: explains a failed simulation of the study from its logs, for a
// simulation run on another server (Antares Web has no job for it). The user gives the logs
// (file or pasted text), then gets the probable causes and the explanation of the assistant.
// Nothing is rendered if the server has no assistant.
function LogsExplanation({ studyId }: Props) {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  // A log file can be huge: its text is never put in the text field, only its last lines are shown
  const [file, setFile] = useState<LogFile | null>(null);
  const [pastedLogs, setPastedLogs] = useState("");
  const [solverVersion, setSolverVersion] = useState("");
  const [fileError, setFileError] = useState("");
  const [state, setState] = useState<JobExplanationState>(INITIAL_EXPLANATION_STATE);
  const controllerRef = useRef<AbortController | null>(null);
  const { data: assistant } = useQuery(assistantQueries.status());
  const language = i18n.language?.startsWith("fr") ? "fr" : "en";

  useEffect(() => {
    return () => controllerRef.current?.abort();
  }, []);

  if (!assistant?.available) {
    return null;
  }

  const { status } = state;
  const isRunning = status === "running";
  const logs = file ? file.text : pastedLogs;

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const stop = () => {
    controllerRef.current?.abort();
    controllerRef.current = null;
  };

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleExplain = async () => {
    stop();
    const controller = new AbortController();
    controllerRef.current = controller;
    setState(RUNNING_EXPLANATION_STATE);

    try {
      await streamLogsExplanation({
        studyId,
        logs,
        fileName: file ? file.name : PASTED_LOGS_FILE_NAME,
        solverVersion: solverVersion.trim() || undefined,
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
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const input = event.target;
    const chosen = input.files?.[0];
    input.value = ""; // The same file can be chosen again
    if (!chosen) {
      return;
    }
    try {
      const text = await readFileText(chosen);
      setFile({
        name: chosen.name,
        text: text.slice(-MAX_LOGS_CHARS),
        isCut: text.length > MAX_LOGS_CHARS,
      });
      setFileError("");
    } catch (err) {
      setFileError(toError(err).message);
    }
  };

  // Back to the form, with the same logs: to fix them or the solver version
  const handleEditLogs = () => {
    stop();
    setState(INITIAL_EXPLANATION_STATE);
  };

  const handleClose = () => {
    setOpen(false);
    if (isRunning) {
      stop();
      setState(INITIAL_EXPLANATION_STATE);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Tooltip title={t("study.explainLogs.tooltip")}>
        <Button
          variant="outlined"
          size="extra-small"
          startIcon={<ReceiptLongOutlinedIcon />}
          onClick={() => setOpen(true)}
        >
          {t("study.explainLogs.button")}
        </Button>
      </Tooltip>
      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>{t("study.explainLogs.title")}</DialogTitle>
        <DialogContent dividers>
          {status === "idle" ? (
            <Stack direction="column" spacing={2}>
              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                {t("study.explainLogs.hint")}
              </Typography>
              <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
                <Button component="label" variant="outlined" startIcon={<UploadFileIcon />}>
                  {t("study.explainLogs.chooseFile")}
                  <input
                    type="file"
                    hidden
                    accept=".log,.txt,text/plain"
                    onChange={handleFileChange}
                    data-testid="logs-file-input"
                  />
                </Button>
                {file && <Chip label={file.name} onDelete={() => setFile(null)} />}
              </Stack>
              {fileError && (
                <Typography variant="body2" color="error">
                  {fileError}
                </Typography>
              )}
              {file ? (
                <Box>
                  <Typography variant="caption" sx={{ color: "text.secondary" }}>
                    {t(file.isCut ? "study.explainLogs.previewCut" : "study.explainLogs.preview", {
                      count: PREVIEW_LINES,
                    })}
                  </Typography>
                  <Box component="pre" sx={PREVIEW_SX}>
                    {file.text.trimEnd().split("\n").slice(-PREVIEW_LINES).join("\n")}
                  </Box>
                </Box>
              ) : (
                <TextField
                  label={t("study.explainLogs.logs")}
                  value={pastedLogs}
                  onChange={(event) => setPastedLogs(event.target.value.slice(-MAX_LOGS_CHARS))}
                  multiline
                  minRows={6}
                  maxRows={14}
                  fullWidth
                  slotProps={{ input: { sx: { fontFamily: "monospace", fontSize: "0.8em" } } }}
                />
              )}
              <TextField
                label={t("study.explainLogs.solverVersion")}
                helperText={t("study.explainLogs.solverVersionHelp")}
                value={solverVersion}
                onChange={(event) => setSolverVersion(event.target.value)}
                size="small"
                sx={{ maxWidth: 260 }}
              />
            </Stack>
          ) : (
            <ExplanationContent state={state} />
          )}
        </DialogContent>
        <DialogActions>
          {status === "idle" && (
            <Button onClick={handleExplain} variant="contained" disabled={!logs.trim()}>
              {t("study.explainLogs.explain")}
            </Button>
          )}
          {!isRunning && status !== "idle" && (
            <>
              <Button onClick={handleEditLogs}>{t("study.explainLogs.editLogs")}</Button>
              <Button startIcon={<ReplayIcon />} onClick={handleExplain}>
                {t("tasks.explain.restart")}
              </Button>
            </>
          )}
          <Button onClick={handleClose} variant={status === "idle" ? "text" : "contained"}>
            {t(isRunning ? "global.cancel" : "global.close")}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export default LogsExplanation;
