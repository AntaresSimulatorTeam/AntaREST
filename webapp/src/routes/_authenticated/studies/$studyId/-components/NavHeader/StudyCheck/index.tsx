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

import AssistantThread from "@/components/AssistantConversation/AssistantThread";
import useAssistantRun from "@/components/AssistantConversation/useAssistantRun";
import useAssistantThreads from "@/components/AssistantConversation/useAssistantThreads";
import { assistantQueries } from "@/queries/assistant/queries";
import { streamStudyCheck } from "@/services/api/assistant";
import type { CheckFinding } from "@/services/api/assistant/types";
import CloseIcon from "@mui/icons-material/Close";
import FactCheckOutlinedIcon from "@mui/icons-material/FactCheckOutlined";
import ReplayIcon from "@mui/icons-material/Replay";
import {
  Alert,
  AlertTitle,
  Badge,
  Box,
  Button,
  CircularProgress,
  Divider,
  Drawer,
  IconButton,
  Skeleton,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import Markdown from "react-markdown";
import CheckProgress from "./CheckProgress";
import FindingsList from "./FindingsList";
import { buildFindingContext, countIssues, INITIAL_CHECK_STATE, reduceCheckEvent } from "./utils";

interface Props {
  studyId: string;
}

// Button to check the consistency of a study with the AI assistant, and the panel showing the
// progress while it runs, then the findings of the rules and the analysis of the assistant. The
// findings are shown as soon as the rules have run, before the analysis is written, and each one
// has its own conversation with the assistant. Nothing is rendered if the server has no assistant.
//
// The result is kept while the user stays on the study: the button then shows the number of
// findings to look at, and opens the result again. So are the conversations about the findings.
function StudyCheck({ studyId }: Props) {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const { data: assistant } = useQuery(assistantQueries.status());
  // The assistant writes its analysis in the language of the interface
  const language = i18n.language?.startsWith("fr") ? "fr" : "en";
  const { state, start, cancel } = useAssistantRun(
    INITIAL_CHECK_STATE,
    reduceCheckEvent,
    (handlers) => streamStudyCheck({ studyId, language, ...handlers }),
  );
  const threads = useAssistantThreads(studyId);

  if (!assistant?.available) {
    return null;
  }

  const { status, report, reportError, answer, error, extraTools } = state;
  const isRunning = status === "running";
  const hasFindings = !!report && report.findings.length > 0;
  const canModify = !assistant.readOnly;

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleClick = () => {
    setOpen(true);

    if (status === "idle") {
      start();
    }
  };

  const handleRestart = () => {
    // The conversations are about the findings of the previous check
    threads.reset();
    start();
  };

  const handleCancel = () => {
    cancel();
    setOpen(false);
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const getDiscussionHint = () => {
    if (isRunning) {
      return t("study.check.finding.waitForCheck");
    }
    return canModify ? undefined : t("study.check.finding.readOnlyHint");
  };

  const renderDiscussion = (id: string, finding: CheckFinding) => (
    <AssistantThread
      thread={threads.threads[id]}
      onSend={(message) =>
        threads.send(id, {
          message,
          context: buildFindingContext(finding),
          // The assistant already knows the study and the findings: the conversation goes on
          baseHistory: state.history,
        })
      }
      onStop={() => threads.stop(id)}
      placeholder={t(canModify ? "study.check.finding.ask" : "study.check.finding.askReadOnly")}
      // A conversation continues the one of the check: it waits for its end
      disabled={isRunning}
      hint={getDiscussionHint()}
    />
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Tooltip title={t("study.check.tooltip")}>
        <Badge
          badgeContent={countIssues(report)}
          color={report?.summary.error ? "error" : "warning"}
          invisible={isRunning}
          // Kept inside the button: the header clips what overflows at its top
          sx={{ "& .MuiBadge-badge": { top: 4, right: 4 } }}
        >
          <Button
            variant="outlined"
            size="extra-small"
            startIcon={
              isRunning ? <CircularProgress size={14} color="inherit" /> : <FactCheckOutlinedIcon />
            }
            onClick={handleClick}
          >
            {t("study.check.button")}
          </Button>
        </Badge>
      </Tooltip>
      <Drawer
        anchor="right"
        open={open}
        onClose={() => setOpen(false)}
        slotProps={{ paper: { sx: { width: { xs: "100vw", sm: 560 } } } }}
      >
        <Toolbar sx={{ justifyContent: "space-between", gap: 1 }}>
          <Typography variant="h6" component="h2">
            {t("study.check.title")}
          </Typography>
          <IconButton onClick={() => setOpen(false)} aria-label={t("global.close")}>
            <CloseIcon />
          </IconButton>
        </Toolbar>
        <Divider />
        <Stack direction="column" spacing={3} sx={{ p: 2, overflow: "auto", flex: 1 }}>
          {isRunning && <CheckProgress state={state} onCancel={handleCancel} />}

          {threads.hasChangedData && !isRunning && (
            <Alert severity="info">{t("study.check.outdated")}</Alert>
          )}

          {status === "error" && (
            <Alert severity="error">
              <AlertTitle>{t("study.check.failed")}</AlertTitle>
              {error}
            </Alert>
          )}

          {reportError !== undefined && (
            <Alert severity="warning">
              <AlertTitle>{t("study.check.rulesFailed")}</AlertTitle>
              {reportError}
            </Alert>
          )}

          {report && (
            <Box component="section">
              <Typography variant="subtitle1" component="h3" sx={{ mb: 1, fontWeight: "bold" }}>
                {t("study.check.findings")}
              </Typography>
              <FindingsList report={report} renderDiscussion={renderDiscussion} />
            </Box>
          )}

          {(answer || (isRunning && state.phase === "reporting" && hasFindings)) && (
            <Box component="section">
              <Typography variant="subtitle1" component="h3" sx={{ fontWeight: "bold" }}>
                {t("study.check.analysis")}
              </Typography>
              {answer ? (
                <>
                  <Box
                    sx={{
                      typography: "body2",
                      overflowWrap: "anywhere",
                      "& code": { fontSize: "0.9em" },
                    }}
                  >
                    <Markdown>{answer}</Markdown>
                  </Box>
                  <Typography variant="caption" sx={{ color: "text.secondary" }}>
                    {t("study.check.aiDisclaimer")}
                  </Typography>
                </>
              ) : (
                <>
                  <Typography variant="body2" sx={{ color: "text.secondary", my: 1 }}>
                    {extraTools.length > 0
                      ? t("study.check.analysisDigging", { count: extraTools.length })
                      : t("study.check.analysisPending")}
                  </Typography>
                  <Skeleton />
                  <Skeleton />
                  <Skeleton width="60%" />
                </>
              )}
            </Box>
          )}
        </Stack>
        {!isRunning && status !== "idle" && (
          <>
            <Divider />
            <Stack direction="row" sx={{ p: 2, justifyContent: "flex-end" }}>
              <Button variant="outlined" startIcon={<ReplayIcon />} onClick={handleRestart}>
                {t("study.check.restart")}
              </Button>
            </Stack>
          </>
        )}
      </Drawer>
    </>
  );
}

export default StudyCheck;
