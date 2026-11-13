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

import CloseIcon from "@mui/icons-material/Close";
import ReplayIcon from "@mui/icons-material/Replay";
import {
  Alert,
  AlertTitle,
  Box,
  Button,
  Divider,
  Drawer,
  IconButton,
  Skeleton,
  Stack,
  Toolbar,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import Markdown from "react-markdown";
import CheckProgress from "./CheckProgress";
import FindingsList from "./FindingsList";
import type { StudyCheckState } from "./utils";

interface Props {
  open: boolean;
  state: StudyCheckState;
  onClose: VoidFunction;
  onStart: VoidFunction;
  onCancel: VoidFunction;
}

// Panel of the study check: progress while it runs, then the findings of the rules and the
// analysis of the assistant. The findings are shown as soon as the rules have run, before the
// analysis is written.
function StudyCheckDrawer({ open, state, onClose, onStart, onCancel }: Props) {
  const { t } = useTranslation();
  const { status, report, reportError, answer, error, extraTools } = state;
  const isRunning = status === "running";
  const hasFindings = !!report && report.findings.length > 0;

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      slotProps={{ paper: { sx: { width: { xs: "100vw", sm: 560 } } } }}
    >
      <Toolbar sx={{ justifyContent: "space-between", gap: 1 }}>
        <Typography variant="h6" component="h2">
          {t("study.check.title")}
        </Typography>
        <IconButton onClick={onClose} aria-label={t("global.close")}>
          <CloseIcon />
        </IconButton>
      </Toolbar>
      <Divider />
      <Stack direction="column" spacing={3} sx={{ p: 2, overflow: "auto", flex: 1 }}>
        {isRunning && <CheckProgress state={state} onCancel={onCancel} />}

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
            <FindingsList report={report} />
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
            <Button variant="outlined" startIcon={<ReplayIcon />} onClick={onStart}>
              {t("study.check.restart")}
            </Button>
          </Stack>
        </>
      )}
    </Drawer>
  );
}

export default StudyCheckDrawer;
