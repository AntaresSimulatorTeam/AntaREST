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

import RouterLink from "@/components/router/RouterLink";
import { isTextTruncated } from "@/utils/domUtils";
import { Tooltip } from "@mui/material";
import { type ToOptions } from "@tanstack/react-router";
import React, { useLayoutEffect, useRef, useState } from "react";

interface BreadcrumbLinkProps {
  label: string;
  icon: React.ReactNode;
  truncate?: boolean;
  linkOptions: ToOptions;
  onClick: () => void;
}

const truncatedTextStyle = {
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
  maxWidth: 180,
} as const;

const linkStyle = {
  display: "flex",
  alignItems: "center",
  transition: "color 0.15s ease",
  "&:hover": {
    color: "secondary.main",
  },
} as const;

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
      ref={(e) => {
        //
      }}
      underline="hover"
      color="inherit"
      onClick={onClick}
      sx={linkStyle}
      {...linkOptions}
    >
      {icon}
      <span ref={textRef} style={truncate ? truncatedTextStyle : undefined}>
        {label}
      </span>
    </RouterLink>
  );

  return isTruncated ? <Tooltip title={label}>{linkContent}</Tooltip> : linkContent;
}

export default BreadcrumbLink;
