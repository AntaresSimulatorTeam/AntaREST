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
  Chip,
  Stack,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";

const SEVERITIES: CheckSeverity[] = ["error", "warning", "info"];

const SEVERITY_ICONS: Record<CheckSeverity, React.ReactElement> = {
  error: <ErrorOutlineIcon color="error" fontSize="small" />,
  warning: <WarningAmberIcon color="warning" fontSize="small" />,
  info: <InfoOutlinedIcon color="info" fontSize="small" />,
};

interface FindingProps {
  finding: CheckFinding;
}

function Finding({ finding }: FindingProps) {
  const { t } = useTranslation();
  const hiddenObjects = finding.count - finding.objects.length;

  return (
    <Accordion disableGutters variant="outlined">
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack direction="row" spacing={1} sx={{ alignItems: "center", minWidth: 0 }}>
          {SEVERITY_ICONS[finding.severity]}
          <Typography variant="body2" sx={{ fontWeight: "bold" }}>
            {t(`study.check.rule.${finding.rule}`, { defaultValue: finding.rule })}
          </Typography>
          <Chip label={finding.count} size="small" />
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        <Typography variant="body2">{finding.message}</Typography>
        <Typography variant="caption" sx={{ display: "block", mt: 1.5, color: "text.secondary" }}>
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
      </AccordionDetails>
    </Accordion>
  );
}

interface Props {
  report: CheckReport;
}

// Findings of the consistency rules, most severe first.
function FindingsList({ report }: Props) {
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
        {report.findings.map((finding, index) => (
          // A rule can report several findings: the index tells them apart, the list never changes
          <Finding key={`${finding.rule}-${index}`} finding={finding} />
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
