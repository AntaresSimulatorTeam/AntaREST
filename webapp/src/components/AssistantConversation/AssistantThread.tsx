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

import { Stack, Typography } from "@mui/material";
import ConversationInput from "./ConversationInput";
import ConversationTurn from "./ConversationTurn";
import { INITIAL_CHAT_STATE, type ChatState } from "./utils";

interface Props {
  /** State of the conversation; nothing has been asked yet if it is not given. */
  thread?: ChatState;
  onSend: (message: string) => void;
  onStop: VoidFunction;
  placeholder: string;
  disabled?: boolean;
  /** Shown under the field: what the assistant can do here, or why the field is disabled. */
  hint?: string;
}

// A conversation with the AI assistant about one subject, to put next to that subject: the
// messages already exchanged, then the field to write the next one. See `useAssistantThreads`.
function AssistantThread({
  thread = INITIAL_CHAT_STATE,
  onSend,
  onStop,
  placeholder,
  disabled,
  hint,
}: Props) {
  return (
    <Stack direction="column" spacing={1.5}>
      {thread.turns.map((turn, index) => (
        <ConversationTurn
          key={turn.id}
          turn={turn}
          isRunning={thread.isRunning && index === thread.turns.length - 1}
        />
      ))}
      <ConversationInput
        isRunning={thread.isRunning}
        onSend={onSend}
        onStop={onStop}
        placeholder={placeholder}
        disabled={disabled}
      />
      {hint && (
        <Typography variant="caption" sx={{ color: "text.secondary" }}>
          {hint}
        </Typography>
      )}
    </Stack>
  );
}

export default AssistantThread;
