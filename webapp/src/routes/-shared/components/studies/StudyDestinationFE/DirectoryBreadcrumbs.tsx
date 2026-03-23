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

import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import HomeIcon from "@mui/icons-material/Home";
import { Box, ButtonBase, Divider, IconButton, InputBase, Tooltip } from "@mui/material";
import React from "react";
import { useTranslation } from "react-i18next";
import {
  directoryBreadcrumbsSx,
  getBreadcrumbSegmentSx,
  breadcrumbTrackSx,
  getNewDirectoryInputSx,
} from "./styles";
import type { BreadcrumbSegment } from "./types";

interface Props {
  breadcrumbs: BreadcrumbSegment[];
  newSubdirectoriesPath: string;
  disabled: boolean;
  canGoUp: boolean;
  /** Forwarded ref for the InputBase inside the breadcrumbs bar. */
  inputRef?: React.Ref<HTMLInputElement>;
  name?: string;
  onGoUp: () => void;
  onBreadcrumbClick: (segment: BreadcrumbSegment) => void;
  onNewPathChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  /** Handles Backspace-to-go-up and any other key behaviour on the input. */
  onNewPathKeyDown: (event: React.KeyboardEvent<HTMLInputElement>) => void;
}

function DirectoryBreadcrumbs({
  breadcrumbs,
  newSubdirectoriesPath,
  disabled,
  canGoUp,
  inputRef,
  name,
  onGoUp,
  onBreadcrumbClick,
  onNewPathChange,
  onNewPathKeyDown,
}: Props) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={directoryBreadcrumbsSx}>
      <Tooltip title={t("studies.destination.goUp")} placement="top">
        {/* Wrapping span keeps the Tooltip working when the button is disabled */}
        <span>
          <IconButton
            size="small"
            onClick={onGoUp}
            disabled={!canGoUp || disabled}
            aria-label={t("studies.destination.goUp")}
          >
            <ArrowUpwardIcon sx={{ fontSize: 16 }} />
          </IconButton>
        </span>
      </Tooltip>

      <Divider orientation="vertical" flexItem />

      {/* Breadcrumb track + new directory input */}
      <Box sx={breadcrumbTrackSx}>
        {breadcrumbs.map((segment: BreadcrumbSegment, index: number) => (
          // Key is safe: only the root segment has a null id, and there's only one root per breadcrumb trail
          <React.Fragment key={segment.id ?? "__root__"}>
            {index > 0 && (
              <ChevronRightIcon sx={{ fontSize: 13, color: "text.disabled", flexShrink: 0 }} />
            )}
            <ButtonBase
              onClick={() => onBreadcrumbClick(segment)}
              disabled={disabled}
              aria-label={segment.name}
              sx={getBreadcrumbSegmentSx(!!segment.active)}
            >
              {index === 0 && <HomeIcon sx={{ fontSize: 13 }} />}
              {segment.name}
            </ButtonBase>
          </React.Fragment>
        ))}

        <ChevronRightIcon sx={{ fontSize: 13, color: "text.disabled", flexShrink: 0 }} />

        {/* New sub-directory inline input */}
        <InputBase
          inputRef={inputRef}
          name={name}
          value={newSubdirectoriesPath}
          onChange={onNewPathChange}
          onKeyDown={onNewPathKeyDown}
          disabled={disabled}
          placeholder={t("studies.destination.newDirectoryPath")}
          sx={getNewDirectoryInputSx(!!newSubdirectoriesPath)}
          inputProps={{
            "aria-label": t("studies.destination.newDirectoryPath"),
          }}
        />
      </Box>
    </Box>
  );
}

export default DirectoryBreadcrumbs;
