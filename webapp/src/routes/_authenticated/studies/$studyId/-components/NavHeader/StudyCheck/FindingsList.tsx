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

import type { CheckFinding, CheckReport, CheckSeverity } from "@/services/api/assistant/types";
import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Button,
  Chip,
  Stack,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import AssistantReport from "./AssistantReport";
import {
  groupFindingsByRule,
  INITIAL_REPORT_STATE,
  SEVERITIES,
  type AssistantReportState,
  type RuleGroup,
} from "./utils";

const SEVERITY_ICONS: Record<CheckSeverity, React.ReactElement> = {
  error: <ErrorOutlineIcon color="error" fontSize="small" />,
  warning: <WarningAmberIcon color="warning" fontSize="small" />,
  info: <InfoOutlinedIcon color="info" fontSize="small" />,
};

interface FindingProps {
  finding: CheckFinding;
  /** Shown when the rule reports several findings, of different severities. */
  showSeverity: boolean;
}

function Finding({ finding, showSeverity }: FindingProps) {
  const { t } = useTranslation();
  const hiddenObjects = finding.count - finding.objects.length;

  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ alignItems: "flex-start" }}>
        {showSeverity && SEVERITY_ICONS[finding.severity]}
        <Typography variant="body2">{finding.message}</Typography>
      </Stack>
      <Typography variant="caption" sx={{ display: "block", mt: 1, color: "text.secondary" }}>
        {t("study.check.objects", { count: finding.count })}
      </Typography>
      <Box
        component="ul"
        sx={{ m: 0, pl: 2.5, maxHeight: 200, overflow: "auto", overflowWrap: "anywhere" }}
      >
        {finding.objects.map((object) => (
          <Typography key={object} component="li" variant="body2">
            {object}
          </Typography>
        ))}
        {hiddenObjects > 0 && (
          <Typography component="li" variant="body2" sx={{ color: "text.secondary" }}>
            {t("study.check.moreObjects", { count: hiddenObjects })}
          </Typography>
        )}
      </Box>
    </Box>
  );
}

interface RuleProps {
  group: RuleGroup;
  /** Explanation of the rule by the AI assistant, once the user asked for it. */
  explanation: AssistantReportState;
  onExplain: VoidFunction;
  /** Conversation with the AI assistant about the rule. */
  children: React.ReactNode;
}

function Rule({ group, explanation, onExplain, children }: RuleProps) {
  const { t } = useTranslation();
  const id = `rule-${group.rule}`;

  return (
    <Accordion disableGutters variant="outlined">
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        id={`${id}-header`}
        aria-controls={`${id}-content`}
      >
        <Stack direction="row" spacing={1} sx={{ alignItems: "center", minWidth: 0 }}>
          {SEVERITY_ICONS[group.severity]}
          <Typography variant="body2" sx={{ fontWeight: "bold" }}>
            {t(`study.check.rule.${group.rule}`, { defaultValue: group.rule })}
          </Typography>
          <Chip label={group.count} size="small" />
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        <Stack direction="column" spacing={2}>
          {group.findings.map((finding) => (
            <Finding
              key={`${finding.severity}-${finding.message}`}
              finding={finding}
              showSeverity={group.findings.length > 1}
            />
          ))}
          <Box>
            {explanation.status !== "running" && explanation.status !== "success" && (
              <Button
                variant="outlined"
                size="extra-small"
                startIcon={<AutoAwesomeOutlinedIcon />}
                onClick={onExplain}
                sx={{ mb: explanation.status === "error" ? 1 : 0 }}
              >
                {t("study.check.explain.button")}
              </Button>
            )}
            <AssistantReport
              state={explanation}
              pendingText={t("study.check.explain.pending")}
              failedText={t("study.check.explain.failed")}
              disclaimer={t("study.check.explain.disclaimer")}
            />
          </Box>
          {children}
        </Stack>
      </AccordionDetails>
    </Accordion>
  );
}

interface Props {
  report: CheckReport;
  /** Explanations of the AI assistant, by rule: only those the user asked for. */
  explanations: Record<string, AssistantReportState>;
  onExplain: (group: RuleGroup) => void;
  /** Renders the conversation with the AI assistant about a rule. */
  renderDiscussion: (group: RuleGroup) => React.ReactNode;
}

// Findings of the consistency rules, one block per rule, most severe first. They are shown as the
// rules give them: the AI assistant only writes about the rules the user wants explained.
function FindingsList({ report, explanations, onExplain, renderDiscussion }: Props) {
  const { t } = useTranslation();

  if (report.findings.length === 0) {
    return <Alert severity="success">{t("study.check.noFinding")}</Alert>;
  }

  return (
    <Stack direction="column" spacing={1.5}>
      <Stack direction="row" spacing={1}>
        {SEVERITIES.filter((severity) => report.summary[severity] > 0).map((severity) => (
          <Chip
            key={severity}
            icon={SEVERITY_ICONS[severity]}
            label={`${t(`study.check.severity.${severity}`)} : ${report.summary[severity]}`}
            variant="outlined"
            size="small"
          />
        ))}
      </Stack>
      <Box>
        {groupFindingsByRule(report.findings).map((group) => (
          <Rule
            key={group.rule}
            group={group}
            explanation={explanations[group.rule] ?? INITIAL_REPORT_STATE}
            onExplain={() => onExplain(group)}
          >
            {renderDiscussion(group)}
          </Rule>
        ))}
      </Box>
      {report.notes.map((note) => (
        <Alert key={note} severity="info">
          {note}
        </Alert>
      ))}
    </Stack>
  );
}

export default FindingsList;
