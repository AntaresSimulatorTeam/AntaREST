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

import { Box, Tooltip } from "@mui/material";
import type { ToOptions } from "@tanstack/react-router";
import { useLayoutEffect, useRef, useState } from "react";
import RouterLink from "@/components/router/RouterLink";
import { isTextTruncated } from "@/utils/domUtils";
import { truncateTextSx } from "@/utils/muiUtils";

interface BreadcrumbLinkProps {
  label: string;
  icon: React.ReactNode;
  truncate?: boolean;
  linkOptions: ToOptions;
  onClick: () => void;
}

function BreadcrumbLink({
  label,
  icon,
  truncate = false,
  linkOptions,
  onClick,
}: BreadcrumbLinkProps) {
  const textRef = useRef<HTMLSpanElement>(null);
  const [isTruncated, setIsTruncated] = useState(false);

  useLayoutEffect(() => {
    if (!truncate || !textRef.current) {
      setIsTruncated(false);
      return;
    }
    setIsTruncated(isTextTruncated(textRef.current));
  }, [truncate]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const linkContent = (
    <RouterLink
      underline="hover"
      color="inherit"
      onClick={onClick}
      sx={{ display: "flex", alignItems: "center" }}
      {...linkOptions}
    >
      {icon}
      <Box component="span" ref={textRef} sx={[truncate && truncateTextSx(180)]}>
        {label}
      </Box>
    </RouterLink>
  );

  return isTruncated ? <Tooltip title={label}>{linkContent}</Tooltip> : linkContent;
}

export default BreadcrumbLink;
