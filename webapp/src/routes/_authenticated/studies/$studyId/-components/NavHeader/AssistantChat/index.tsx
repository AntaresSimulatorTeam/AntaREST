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

import ConversationInput from "@/components/AssistantConversation/ConversationInput";
import ConversationTurn from "@/components/AssistantConversation/ConversationTurn";
import useAssistantThreads from "@/components/AssistantConversation/useAssistantThreads";
import { INITIAL_CHAT_STATE } from "@/components/AssistantConversation/utils";
import { assistantQueries } from "@/queries/assistant/queries";
import AddCommentOutlinedIcon from "@mui/icons-material/AddCommentOutlined";
import CloseIcon from "@mui/icons-material/Close";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import {
  Box,
  Button,
  Chip,
  Divider,
  Drawer,
  IconButton,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

/** The conversation of the panel is one thread. */
const THREAD = "chat";

interface Props {
  studyId: string;
}

// Button and panel to talk with the AI assistant about the current study: the assistant answers
// with the tools of the MCP server, and can modify the study if the server allows it.
// The tool calls it makes are shown under each message. Nothing is rendered if the server has
// no assistant.
function AssistantChat({ studyId }: Props) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const { threads, send, stop, reset } = useAssistantThreads(studyId);
  const state = threads[THREAD] ?? INITIAL_CHAT_STATE;
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const { data: assistant } = useQuery(assistantQueries.status());

  // Keep the last message visible
  useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ block: "end" });
  }, [state]);

  if (!assistant?.available) {
    return null;
  }

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Tooltip title={t("study.assistant.tooltip")}>
        <Button
          variant="outlined"
          size="extra-small"
          startIcon={<SmartToyOutlinedIcon />}
          onClick={() => setOpen(true)}
        >
          {t("study.assistant.button")}
        </Button>
      </Tooltip>
      <Drawer
        anchor="right"
        open={open}
        onClose={() => setOpen(false)}
        slotProps={{ paper: { sx: { width: { xs: "100vw", sm: 560 } } } }}
      >
        <Toolbar sx={{ justifyContent: "space-between", gap: 1 }}>
          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <Typography variant="h6" component="h2">
              {t("study.assistant.title")}
            </Typography>
            <Chip
              label={t(
                assistant.readOnly ? "study.assistant.readOnly" : "study.assistant.readWrite",
              )}
              color={assistant.readOnly ? "default" : "warning"}
              variant="outlined"
              size="small"
            />
          </Stack>
          <Box>
            <Tooltip title={t("study.assistant.newConversation")}>
              <span>
                <IconButton
                  onClick={reset}
                  disabled={state.turns.length === 0}
                  aria-label={t("study.assistant.newConversation")}
                >
                  <AddCommentOutlinedIcon />
                </IconButton>
              </span>
            </Tooltip>
            <IconButton onClick={() => setOpen(false)} aria-label={t("global.close")}>
              <CloseIcon />
            </IconButton>
          </Box>
        </Toolbar>
        <Divider />
        <Stack direction="column" spacing={3} sx={{ p: 2, overflow: "auto", flex: 1 }}>
          {state.turns.length === 0 && (
            <Typography variant="body2" sx={{ color: "text.secondary", whiteSpace: "pre-line" }}>
              {t(assistant.readOnly ? "study.assistant.hintReadOnly" : "study.assistant.hint")}
            </Typography>
          )}
          {state.turns.map((turn, index) => (
            <ConversationTurn
              key={turn.id}
              turn={turn}
              isRunning={state.isRunning && index === state.turns.length - 1}
            />
          ))}
          <div ref={bottomRef} />
        </Stack>
        <Divider />
        <Box sx={{ p: 2 }}>
          <ConversationInput
            isRunning={state.isRunning}
            onSend={(message) => send(THREAD, { message })}
            onStop={() => stop(THREAD)}
            placeholder={t("study.assistant.placeholder")}
            autoFocus
          />
        </Box>
      </Drawer>
    </>
  );
}

export default AssistantChat;
