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
import FactCheckOutlinedIcon from "@mui/icons-material/FactCheckOutlined";
import { Badge, Button, CircularProgress, Tooltip } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import StudyCheckDrawer from "./StudyCheckDrawer";
import useStudyCheck from "./useStudyCheck";
import { countIssues } from "./utils";

interface Props {
  studyId: string;
}

// Button to check the consistency of a study with the AI assistant, and the panel showing the
// progress and the result. Nothing is rendered if the server has no assistant.
//
// The result is kept while the user stays on the study: the button then shows the number of
// findings to look at, and opens the result again.
function StudyCheck({ studyId }: Props) {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const { data: assistant } = useQuery(assistantQueries.status());
  const { state, start, cancel } = useStudyCheck(
    studyId,
    // The assistant writes its analysis in the language of the interface
    i18n.language?.startsWith("fr") ? "fr" : "en",
  );

  if (!assistant?.available) {
    return null;
  }

  const isRunning = state.status === "running";
  const issues = countIssues(state.report);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleClick = () => {
    setOpen(true);

    if (state.status === "idle") {
      start();
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Tooltip title={t("study.check.tooltip")}>
        <Badge
          badgeContent={issues}
          color={state.report?.summary.error ? "error" : "warning"}
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
      <StudyCheckDrawer
        open={open}
        state={state}
        onClose={() => setOpen(false)}
        onStart={start}
        onCancel={() => {
          cancel();
          setOpen(false);
        }}
      />
    </>
  );
}

export default StudyCheck;
