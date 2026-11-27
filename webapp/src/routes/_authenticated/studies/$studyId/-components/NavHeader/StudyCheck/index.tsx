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
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { assistantQueries } from "@/queries/assistant/queries";
import { streamCheckSummary, streamStudyCheck, streamStudyReview } from "@/services/api/assistant";
import { toError } from "@/utils/fnUtils";
import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";
import CloseIcon from "@mui/icons-material/Close";
import FactCheckOutlinedIcon from "@mui/icons-material/FactCheckOutlined";
import PictureAsPdfOutlinedIcon from "@mui/icons-material/PictureAsPdfOutlined";
import ReplayIcon from "@mui/icons-material/Replay";
import TravelExploreIcon from "@mui/icons-material/TravelExplore";
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
  Stack,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import Markdown from "react-markdown";
import AssistantReport from "./AssistantReport";
import CheckProgress from "./CheckProgress";
import FindingsList from "./FindingsList";
import { buildReportDocument } from "./pdf/buildReportDocument";
import { buildReportFileName } from "./pdf/buildReportFileName";
import { downloadPdf } from "./pdf/downloadPdf";
import useRuleExplanations from "./useRuleExplanations";
import {
  buildRuleContext,
  countIssues,
  getFinishedAnswer,
  getFinishedAnswers,
  getVerdictSeverity,
  INITIAL_CHECK_STATE,
  INITIAL_REPORT_STATE,
  INITIAL_REVIEW_STATE,
  reduceCheckEvent,
  reduceReportEvent,
  reduceReviewEvent,
  type RuleGroup,
} from "./utils";

interface Props {
  studyId: string;
  studyName: string;
}

// Button to check the consistency of a study, and the panel showing the progress of the rules,
// then their findings, grouped by rule, and the verdict. Nothing is rendered if the server has no
// assistant.
//
// The check itself does not call the AI model: the findings and the verdict come from
// deterministic rules, at once. The model only writes when the user asks for it:
// - the explanation of one rule, with a conversation to go further;
// - a summary of all the findings;
// - a review of the study beyond the rules (values out of line with comparable objects), slower
//   and less certain.
//
// The result is kept while the user stays on the study: the button then shows the number of
// findings to look at, and opens the result again. So are the texts of the assistant.
function StudyCheck({ studyId, studyName }: Props) {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const [isDownloadingReport, setIsDownloadingReport] = useState(false);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { data: assistant } = useQuery(assistantQueries.status());
  // The assistant writes in the language of the interface
  const language = i18n.language?.startsWith("fr") ? "fr" : "en";
  const { state, start, cancel } = useAssistantRun(
    INITIAL_CHECK_STATE,
    reduceCheckEvent,
    (handlers) => streamStudyCheck({ studyId, language, ...handlers }),
  );
  const findings = state.report?.findings ?? [];
  const summary = useAssistantRun(INITIAL_REPORT_STATE, reduceReportEvent, (handlers) =>
    streamCheckSummary({ studyId, language, findings, ...handlers }),
  );
  const review = useAssistantRun(INITIAL_REVIEW_STATE, reduceReviewEvent, (handlers) =>
    streamStudyReview({ studyId, language, findings, ...handlers }),
  );
  const {
    explanations,
    explain,
    reset: resetExplanations,
  } = useRuleExplanations(studyId, language);
  const threads = useAssistantThreads(studyId);

  if (!assistant?.available) {
    return null;
  }

  const { status, report, reportError, verdict, error } = state;
  const isRunning = status === "running";
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
    // What the assistant wrote is about the findings of the previous check
    threads.reset();
    resetExplanations();
    summary.reset();
    review.reset();
    start();
  };

  const handleCancel = () => {
    cancel();
    setOpen(false);
  };

  const handleDownloadReport = async () => {
    if (!report) {
      return;
    }
    const generatedAt = new Date();
    const document = buildReportDocument(
      {
        studyId,
        studyName,
        generatedAt,
        language,
        report,
        verdict,
        explanations: getFinishedAnswers(explanations),
        summary: getFinishedAnswer(summary.state),
        review: getFinishedAnswer(review.state),
      },
      t,
    );
    setIsDownloadingReport(true);

    try {
      await downloadPdf(document, buildReportFileName(studyName, generatedAt, t));
    } catch (err) {
      enqueueErrorSnackbar(t("study.check.pdf.failed"), toError(err));
    } finally {
      setIsDownloadingReport(false);
    }
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const renderDiscussion = (group: RuleGroup) => (
    <AssistantThread
      thread={threads.threads[group.rule]}
      onSend={(message) => threads.send(group.rule, { message, context: buildRuleContext(group) })}
      onStop={() => threads.stop(group.rule)}
      placeholder={t(canModify ? "study.check.finding.ask" : "study.check.finding.askReadOnly")}
      hint={canModify ? undefined : t("study.check.finding.readOnlyHint")}
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

          {report && verdict && report.findings.length > 0 && (
            <Alert severity={getVerdictSeverity(report)} sx={{ "& p": { m: 0 } }}>
              <Markdown>{verdict}</Markdown>
            </Alert>
          )}

          {report && (
            <Box component="section">
              <Typography variant="subtitle1" component="h3" sx={{ mb: 1, fontWeight: "bold" }}>
                {t("study.check.findings")}
              </Typography>
              <FindingsList
                report={report}
                explanations={explanations}
                onExplain={explain}
                renderDiscussion={renderDiscussion}
              />
            </Box>
          )}

          {summary.state.status !== "idle" && (
            <Box component="section">
              <Typography variant="subtitle1" component="h3" sx={{ fontWeight: "bold" }}>
                {t("study.check.summary.title")}
              </Typography>
              <AssistantReport
                state={summary.state}
                pendingText={t("study.check.summary.pending")}
                failedText={t("study.check.explain.failed")}
                disclaimer={t("study.check.summary.disclaimer")}
              />
            </Box>
          )}

          {review.state.status !== "idle" && (
            <Box component="section">
              <Typography variant="subtitle1" component="h3" sx={{ fontWeight: "bold" }}>
                {t("study.check.review.title")}
              </Typography>
              <AssistantReport
                state={review.state}
                pendingText={t("study.check.review.pending", { count: review.state.readings })}
                failedText={t("study.check.explain.failed")}
                disclaimer={t("study.check.review.disclaimer")}
              />
            </Box>
          )}
        </Stack>
        {!isRunning && status !== "idle" && (
          <>
            <Divider />
            <Stack
              direction="row"
              spacing={1}
              sx={{ p: 2, justifyContent: "flex-end", flexWrap: "wrap" }}
              useFlexGap
            >
              {status === "success" && countIssues(report) > 0 && (
                <Tooltip title={t("study.check.summary.tooltip")}>
                  <span>
                    <Button
                      variant="text"
                      startIcon={<AutoAwesomeOutlinedIcon />}
                      disabled={summary.state.status === "running"}
                      onClick={summary.start}
                    >
                      {t("study.check.summary.button")}
                    </Button>
                  </span>
                </Tooltip>
              )}
              {status === "success" && (
                <Tooltip title={t("study.check.review.tooltip")}>
                  <span>
                    <Button
                      variant="text"
                      startIcon={<TravelExploreIcon />}
                      disabled={review.state.status === "running"}
                      onClick={review.start}
                    >
                      {t("study.check.review.button")}
                    </Button>
                  </span>
                </Tooltip>
              )}
              {status === "success" && report && (
                <Tooltip title={t("study.check.pdf.tooltip")}>
                  <span>
                    <Button
                      variant="text"
                      startIcon={
                        isDownloadingReport ? (
                          <CircularProgress size={16} color="inherit" />
                        ) : (
                          <PictureAsPdfOutlinedIcon />
                        )
                      }
                      disabled={isDownloadingReport}
                      onClick={handleDownloadReport}
                    >
                      {t("study.check.pdf.button")}
                    </Button>
                  </span>
                </Tooltip>
              )}
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
