/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { Tooltip } from "@mui/material";
import StarPurple500OutlinedIcon from "@mui/icons-material/StarPurple500Outlined";
import StarOutlineOutlinedIcon from "@mui/icons-material/StarOutlineOutlined";

interface Props {
  isActive: boolean;
  activeTitle: string;
  unactiveTitle: string;
  onToggle: () => void;
}

function StarToggle(props: Props) {
  const { isActive, activeTitle, unactiveTitle, onToggle } = props;
  const StarComponent = isActive ? StarPurple500OutlinedIcon : StarOutlineOutlinedIcon;

  return (
    <Tooltip title={isActive ? activeTitle : unactiveTitle}>
      <StarComponent sx={{ cursor: "pointer", ml: 1 }} onClick={onToggle} color="primary" />
    </Tooltip>
  );
}

export default StarToggle;
