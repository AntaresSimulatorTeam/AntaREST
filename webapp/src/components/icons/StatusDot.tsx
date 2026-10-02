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

import CircleIcon from "@mui/icons-material/Circle";
import type { SvgIconProps } from "@mui/material";

interface StatusDotProps {
  status: "success" | "error" | "info" | "warning" | "disabled";
  size?: SvgIconProps["fontSize"] | "xx-small";
}

function StatusDot({ status, size }: StatusDotProps) {
  return (
    <CircleIcon
      color={status}
      {...(size === "xx-small" ? { sx: { fontSize: "0.5rem" } } : { fontSize: size })}
    />
  );
}

export default StatusDot;
