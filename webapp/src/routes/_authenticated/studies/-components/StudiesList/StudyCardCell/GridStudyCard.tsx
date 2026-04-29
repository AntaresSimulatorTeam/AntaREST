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
import { Box, Card, CardContent, Chip, Divider, Tooltip, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import DirectoryLink from "./DirectoryLink";
import StudyCardActions from "./StudyCardActions";
import StudyMetadataRow from "./StudyMetadataRow";
import StudyOwnerTag from "./StudyOwnerTag";
import StudyTypeIcon from "./StudyTypeIcon";
import {
  cardContentBaseSx,
  cardSx,
  chipSx,
  getStudyColors,
  gridCardContentSx,
  overflowBoxSx,
  rowSx,
  studyTitleBaseSx,
  variantChipSx,
} from "./styles";
import type { StudyCardLayoutProps } from "./types";

function GridStudyCard({
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
      <CardContent
        sx={{
          ...gridCardContentSx,
          ...cardContentBaseSx,
          gap: 0.75,
          justifyContent: "space-between",
        }}
      >
        {/* Row 1: study type icon + title + actions */}
        <Box sx={rowSx}>
          <StudyTypeIcon study={study} />
          <Tooltip title={study.name}>
            <Typography
              noWrap
              variant="h6"
              component="div"
              onClick={onOpen}
              sx={{ ...studyTitleBaseSx, color: titleColor, fontSize: "1rem" }}
            >
              {study.name}
            </Typography>
          </Tooltip>
          <StudyCardActions
            studyId={study.id}
            isSelected={isSelected}
            hasStudiesSelected={hasStudiesSelected}
            onSelectionChange={onSelectionChange}
            onCopyId={onCopyId}
            onMenuOpen={onMenuOpen}
          />
        </Box>

        {/* Row 2: directory link (left) | user name (right) */}
        <Box sx={{ ...rowSx, justifyContent: "space-between" }}>
          <Box sx={overflowBoxSx}>
            {directoryPath && <DirectoryLink name={directoryPath} onClick={onDirectoryClick} />}
          </Box>
          <StudyOwnerTag name={study.owner.name} />
        </Box>

        <Box sx={{ display: "flex", flexDirection: "column", gap: 0.75 }}>
          <Divider sx={{ mx: -1.5 }} />

          {/* Row 3: study chips (left) + metadata (right) */}
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              rowGap: 0.5,
              gap: 1,
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, flexShrink: 0 }}>
              {study.managed ? (
                <Chip label={t("studies.managedStudy")} size="small" color="info" sx={chipSx} />
              ) : (
                <Chip label={study.workspace} size="small" sx={chipSx} />
              )}
              {study.archived && (
                <Chip label={t("studies.archived")} size="small" color="warning" sx={chipSx} />
              )}
              {isVariant && (
                <Chip
                  icon={<CallSplitIcon />}
                  label={t("studies.variant")}
                  size="small"
                  color="primary"
                  sx={variantChipSx}
                />
              )}
            </Box>
            <StudyMetadataRow
              creationDate={study.creationDate}
              modificationDate={study.modificationDate}
              version={study.version}
              noWrap
            />
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export default GridStudyCard;
