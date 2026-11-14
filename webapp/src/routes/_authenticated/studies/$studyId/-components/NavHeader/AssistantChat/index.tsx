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
import { streamAssistantChat } from "@/services/api/assistant";
import { toError } from "@/utils/fnUtils";
import AddCommentOutlinedIcon from "@mui/icons-material/AddCommentOutlined";
import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import SendIcon from "@mui/icons-material/Send";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import StopCircleOutlinedIcon from "@mui/icons-material/StopCircleOutlined";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Drawer,
  IconButton,
  Stack,
  TextField,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import Markdown from "react-markdown";
import {
  INITIAL_CHAT_STATE,
  lastTurnMayHaveChangedData,
  reduceChatEvent,
  startTurn,
  type ChatState,
  type ChatTurn,
  type ToolActivity,
} from "./utils";

const TOOL_ICONS: Record<ToolActivity["status"], React.ReactElement> = {
  running: <CircularProgress size={12} color="inherit" />,
  done: <CheckIcon sx={{ fontSize: 14 }} color="success" />,
  error: <ErrorOutlineIcon sx={{ fontSize: 14 }} color="error" />,
};

interface TurnProps {
  turn: ChatTurn;
  isRunning: boolean;
}

function Turn({ turn, isRunning }: TurnProps) {
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

interface Props {
  studyId: string;
}

// Button and panel to talk with the AI assistant about the current study: the assistant answers
// with the tools of the MCP server, and can modify the study if the server allows it.
// The tool calls it makes are shown under each message. Nothing is rendered if the server has
// no assistant.
function AssistantChat({ studyId }: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [state, setState] = useState<ChatState>(INITIAL_CHAT_STATE);
  const controllerRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const { data: assistant } = useQuery(assistantQueries.status());

  useEffect(() => {
    return () => controllerRef.current?.abort();
  }, []);

  // Keep the last message visible
  useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ block: "end" });
  }, [state]);

  if (!assistant?.available) {
    return null;
  }

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSend = async () => {
    const message = input.trim();

    if (!message || state.isRunning) {
      return;
    }

    const controller = new AbortController();
    controllerRef.current = controller;
    const isCurrent = () => controllerRef.current === controller;
    let latest = startTurn(state, message);
    setInput("");
    setState(latest);

    try {
      await streamAssistantChat({
        message,
        studyId,
        history: state.history,
        signal: controller.signal,
        onEvent: (event) => {
          if (isCurrent()) {
            latest = reduceChatEvent(latest, event);
            setState(latest);
          }
        },
      });

      if (isCurrent() && latest.isRunning) {
        // The stream ended without a final event
        latest = reduceChatEvent(latest, { type: "error", message: t("study.assistant.noAnswer") });
        setState(latest);
      }
    } catch (err) {
      if (isCurrent()) {
        latest = reduceChatEvent(latest, { type: "error", message: toError(err).message });
        setState(latest);
      }
    }

    if (isCurrent() && lastTurnMayHaveChangedData(latest)) {
      // The assistant may have modified the study: reload what is displayed
      queryClient.invalidateQueries();
    }
  };

  const handleStop = () => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setState((prev) =>
      reduceChatEvent(prev, { type: "error", message: t("study.assistant.stopped") }),
    );
  };

  const handleNewConversation = () => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setState(INITIAL_CHAT_STATE);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    // Enter sends, Shift+Enter adds a line
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

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
                  onClick={handleNewConversation}
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
            <Turn
              key={turn.id}
              turn={turn}
              isRunning={state.isRunning && index === state.turns.length - 1}
            />
          ))}
          <div ref={bottomRef} />
        </Stack>
        <Divider />
        <Stack direction="row" spacing={1} sx={{ p: 2, alignItems: "flex-end" }}>
          <TextField
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t("study.assistant.placeholder")}
            multiline
            maxRows={6}
            fullWidth
            size="small"
            autoFocus
            slotProps={{ htmlInput: { "aria-label": t("study.assistant.placeholder") } }}
          />
          {state.isRunning ? (
            <Tooltip title={t("study.assistant.stop")}>
              <IconButton onClick={handleStop} color="error" aria-label={t("study.assistant.stop")}>
                <StopCircleOutlinedIcon />
              </IconButton>
            </Tooltip>
          ) : (
            <Tooltip title={t("study.assistant.send")}>
              <span>
                <IconButton
                  onClick={handleSend}
                  color="primary"
                  disabled={!input.trim()}
                  aria-label={t("study.assistant.send")}
                >
                  <SendIcon />
                </IconButton>
              </span>
            </Tooltip>
          )}
        </Stack>
      </Drawer>
    </>
  );
}

export default AssistantChat;
