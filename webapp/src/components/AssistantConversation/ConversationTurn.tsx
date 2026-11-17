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

import CheckIcon from "@mui/icons-material/Check";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import { Alert, Box, CircularProgress, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import Markdown from "react-markdown";
import type { ChatTurn, ToolActivity } from "./utils";

const TOOL_ICONS: Record<ToolActivity["status"], React.ReactElement> = {
  running: <CircularProgress size={12} color="inherit" />,
  done: <CheckIcon sx={{ fontSize: 14 }} color="success" />,
  error: <ErrorOutlineIcon sx={{ fontSize: 14 }} color="error" />,
};

interface Props {
  turn: ChatTurn;
  isRunning: boolean;
}

// A message of the user, the tool calls made by the assistant to answer it, then its answer.
function ConversationTurn({ turn, isRunning }: Props) {
  const { t } = useTranslation();

  return (
    <Stack direction="column" spacing={1}>
      <Box
        sx={{
          alignSelf: "flex-end",
          maxWidth: "85%",
          px: 1.5,
          py: 1,
          borderRadius: 2,
          bgcolor: "action.selected",
          typography: "body2",
          whiteSpace: "pre-wrap",
          overflowWrap: "anywhere",
        }}
      >
        {turn.question}
      </Box>
      {turn.tools.length > 0 && (
        <Stack direction="column" spacing={0.25} aria-label={t("study.assistant.actions")}>
          {turn.tools.map((tool, index) => (
            <Stack
              // The calls of a turn are only appended: the index is a stable key

              key={index}
              direction="row"
              spacing={0.75}
              sx={{ alignItems: "center", color: "text.secondary" }}
            >
              {TOOL_ICONS[tool.status]}
              <Typography
                variant="caption"
                sx={{ fontFamily: "monospace", overflowWrap: "anywhere" }}
              >
                {tool.label}
              </Typography>
            </Stack>
          ))}
        </Stack>
      )}
      {turn.answer && (
        <Box sx={{ typography: "body2", overflowWrap: "anywhere", "& p:first-of-type": { mt: 0 } }}>
          <Markdown>{turn.answer}</Markdown>
        </Box>
      )}
      {turn.error && <Alert severity="error">{turn.error}</Alert>}
      {isRunning && !turn.answer && !turn.error && (
        <Typography variant="caption" sx={{ color: "text.secondary" }} role="status">
          {t("study.assistant.working")}
        </Typography>
      )}
    </Stack>
  );
}

export default ConversationTurn;
