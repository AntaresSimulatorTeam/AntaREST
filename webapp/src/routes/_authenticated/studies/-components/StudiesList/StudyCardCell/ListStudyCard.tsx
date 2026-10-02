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

import { StudyType } from "@/types/types";
import CallSplitIcon from "@mui/icons-material/CallSplit";
import { Box, Card, CardContent, Chip, Tooltip, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { StudyCardLayoutProps } from "./types";
import {
  cardContentBaseSx,
  cardSx,
  getStudyColors,
  listCardContentSx,
  overflowBoxSx,
  rowSx,
  studyTitleBaseSx,
  variantChipSx,
} from "./styles";
import StudyCardActions from "./StudyCardActions";
import StudyMetadataRow from "./StudyMetadataRow";
import StudyOwnerTag from "./StudyOwnerTag";
import StudyTypeIcon from "./StudyTypeIcon";
import DirectoryLink from "./DirectoryLink";

function ListStudyCard({
  study,
  directoryPath,
  width,
  height,
  isSelected,
  hasStudiesSelected,
  onOpen,
  onDirectoryClick,
  onCopyId,
  onSelectionChange,
  onMenuOpen,
}: StudyCardLayoutProps) {
  const { t } = useTranslation();

  const isVariant = study.type === StudyType.VARIANT;
  const { titleColor, accentColor } = getStudyColors(study);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Card className="StudyCard" elevation={3} sx={cardSx(width, height, accentColor, isSelected)}>
      <CardContent sx={{ ...listCardContentSx, ...cardContentBaseSx, gap: 0.25 }}>
        {/* Line 1: title + actions */}
        <Box sx={rowSx}>
          <StudyTypeIcon study={study} />
          <Tooltip title={study.name}>
            <Typography
              noWrap
              variant="subtitle2"
              component="div"
              onClick={onOpen}
              sx={{ ...studyTitleBaseSx, color: titleColor, minWidth: 0 }}
            >
              {study.name}
            </Typography>
          </Tooltip>
          {isVariant && (
            <Chip
              icon={<CallSplitIcon />}
              label={t("studies.variant")}
              size="small"
              color="primary"
              sx={variantChipSx}
            />
          )}
          <StudyOwnerTag name={study.owner.name} />
          <StudyCardActions
            studyId={study.id}
            isSelected={isSelected}
            hasStudiesSelected={hasStudiesSelected}
            onSelectionChange={onSelectionChange}
            onCopyId={onCopyId}
            onMenuOpen={onMenuOpen}
          />
        </Box>

        {/* Line 2: directory path (left) | metadata (right) */}
        <Box sx={{ ...rowSx, gap: 0 }}>
          <Box sx={overflowBoxSx}>
            {directoryPath && (
              <DirectoryLink name={directoryPath} iconSize={12} onClick={onDirectoryClick} />
            )}
          </Box>
          <StudyMetadataRow
            creationDate={study.creationDate}
            modificationDate={study.modificationDate}
            version={study.version}
          />
        </Box>
      </CardContent>
    </Card>
  );
}

export default ListStudyCard;
