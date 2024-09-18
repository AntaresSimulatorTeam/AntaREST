/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import HighlightOffIcon from "@mui/icons-material/HighlightOff";
import { Box } from "@mui/material";
import { PropsWithChildren } from "react";

interface Props {
  onRemove: () => void;
}

export default function OffsetInput(props: PropsWithChildren<Props>) {
  const { onRemove, children } = props;
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        position: "relative",
      }}
    >
      <HighlightOffIcon
        sx={{
          position: "absolute",
          top: "-15px",
          right: "-25px",
          color: "error.main",
          cursor: "pointer",
          "&:hover": {
            color: "error.light",
          },
        }}
        onClick={onRemove}
      />
      {children}
    </Box>
  );
}
