/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import HelpIcon from "@mui/icons-material/Help";
import { Tooltip, IconButton, type SxProps, type Theme } from "@mui/material";

interface Props {
  to: string;
  sx?: SxProps<Theme>;
}

function DocLink({ to, sx }: Props) {
  return (
    <Tooltip title="View documentation" sx={sx}>
      <IconButton href={to} target="_blank" rel="noopener noreferrer" color="default">
        <HelpIcon />
      </IconButton>
    </Tooltip>
  );
}

export default DocLink;
