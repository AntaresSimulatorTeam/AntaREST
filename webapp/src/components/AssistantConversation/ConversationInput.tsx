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

import SendIcon from "@mui/icons-material/Send";
import StopCircleOutlinedIcon from "@mui/icons-material/StopCircleOutlined";
import { IconButton, Stack, TextField, Tooltip } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

interface Props {
  /** True while the assistant answers: the send button becomes a stop button. */
  isRunning: boolean;
  onSend: (message: string) => void;
  onStop: VoidFunction;
  placeholder: string;
  disabled?: boolean;
  autoFocus?: boolean;
}

// Field to write a message to the assistant: Enter sends, Shift+Enter adds a line.
function ConversationInput({ isRunning, onSend, onStop, placeholder, disabled, autoFocus }: Props) {
  const { t } = useTranslation();
  const [input, setInput] = useState("");
  const message = input.trim();

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSend = () => {
    if (!message || isRunning || disabled) {
      return;
    }

    setInput("");
    onSend(message);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Stack direction="row" spacing={1} sx={{ alignItems: "flex-end" }}>
      <TextField
        value={input}
        onChange={(event) => setInput(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        multiline
        maxRows={6}
        fullWidth
        size="small"
        autoFocus={autoFocus}
        slotProps={{ htmlInput: { "aria-label": placeholder } }}
      />
      {isRunning ? (
        <Tooltip title={t("study.assistant.stop")}>
          <IconButton onClick={onStop} color="error" aria-label={t("study.assistant.stop")}>
            <StopCircleOutlinedIcon />
          </IconButton>
        </Tooltip>
      ) : (
        <Tooltip title={t("study.assistant.send")}>
          <span>
            <IconButton
              onClick={handleSend}
              color="primary"
              disabled={!message || disabled}
              aria-label={t("study.assistant.send")}
            >
              <SendIcon />
            </IconButton>
          </span>
        </Tooltip>
      )}
    </Stack>
  );
}

export default ConversationInput;
