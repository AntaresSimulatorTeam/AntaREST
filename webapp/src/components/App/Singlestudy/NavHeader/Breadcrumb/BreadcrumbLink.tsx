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

import HomeIcon from "@mui/icons-material/Home";
import { Link, Tooltip } from "@mui/material";
import { useLayoutEffect, useRef, useState } from "react";

interface BreadcrumbLinkProps {
  folderName: string;
  isFirstSegment: boolean;
  /**
   * Indicates if this is the study name (last segment).
   * Study names are never truncated to prevent users from accidentally
   * working with the wrong study due to similar truncated names.
   */
  isLastSegment?: boolean;
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
  cursor: "pointer",
  transition: "color 0.15s ease",
  "&:hover": {
    color: "info.main",
  },
} as const;

function BreadcrumbLink({
  folderName,
  isFirstSegment,
  isLastSegment,
  onClick,
}: BreadcrumbLinkProps) {
  const textRef = useRef<HTMLSpanElement>(null);
  const [isTruncated, setIsTruncated] = useState(false);

  // Study names (last segment) are never truncated to avoid user confusion
  const shouldTruncate = !isLastSegment;

  useLayoutEffect(() => {
    if (!shouldTruncate) {
      return;
    }

    const element = textRef.current;
    if (element) {
      setIsTruncated(element.scrollWidth > element.clientWidth);
    }
  }, [shouldTruncate]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const linkContent = (
    <Link underline="hover" color="inherit" onClick={onClick} sx={linkStyle}>
      {isFirstSegment && <HomeIcon fontSize="inherit" sx={{ mr: 1 }} />}
      <span ref={textRef} style={shouldTruncate ? truncatedTextStyle : undefined}>
        {folderName}
      </span>
    </Link>
  );

  return isTruncated ? <Tooltip title={folderName}>{linkContent}</Tooltip> : linkContent;
}

export default BreadcrumbLink;
