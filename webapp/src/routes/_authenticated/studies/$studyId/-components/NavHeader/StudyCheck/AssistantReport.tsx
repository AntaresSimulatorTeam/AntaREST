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

import { Alert, Box, Skeleton, Typography } from "@mui/material";
import Markdown from "react-markdown";
import type { AssistantReportState } from "./utils";

interface Props {
  state: AssistantReportState;
  /** Shown while the assistant writes. */
  pendingText: string;
  /** Shown when the assistant failed without giving a reason. */
  failedText: string;
  /** Reminds what the text is worth: it is written by an AI. */
  disclaimer: string;
}

// A text written by the AI assistant on request (explanation of a rule, summary, review):
// what it is doing while it writes, then its text, always followed by a reminder of its origin.
function AssistantReport({ state, pendingText, failedText, disclaimer }: Props) {
  const { status, answer, error } = state;

  return (
    <>
      {status === "error" && <Alert severity="error">{error || failedText}</Alert>}
      {status === "running" && (
        <Box role="status">
          <Typography variant="body2" sx={{ color: "text.secondary", my: 1 }}>
            {pendingText}
          </Typography>
          <Skeleton />
          <Skeleton width="60%" />
        </Box>
      )}
      {status === "success" && (
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
            {disclaimer}
          </Typography>
        </>
      )}
    </>
  );
}

export default AssistantReport;
