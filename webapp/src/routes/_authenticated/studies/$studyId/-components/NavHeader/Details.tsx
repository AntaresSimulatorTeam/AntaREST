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

import EditorIcon from "@/components/icons/EditorIcon";
import RouterLink from "@/components/router/RouterLink";
import { PUBLIC_MODE_LIST } from "@/components/utils/constants";
import { buildModificationDate, convertUTCToLocalTime } from "@/services/utils";
import type { StudyMetadata } from "@/types/types";
import { truncateTextSx } from "@/utils/muiUtils";
import { compactSemanticVersion } from "@/utils/versionUtils";
import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import AltRouteOutlinedIcon from "@mui/icons-material/AltRouteOutlined";
import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";
import SecurityOutlinedIcon from "@mui/icons-material/SecurityOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import { Box, Divider, Tooltip, Typography, styled } from "@mui/material";
import { useTranslation } from "react-i18next";

const TinyText = styled(Typography)(({ theme }) => ({
  fontSize: 12,
  color: theme.palette.text.secondary,
}));

const StyledDivider = styled(Divider)(({ theme }) => ({
  margin: theme.spacing(0, 1),
  width: "1px",
  height: "20px",
  backgroundColor: theme.palette.divider,
}));

const Item = styled(Box)(({ theme }) => ({
  display: "flex",
  gap: theme.spacing(1),
  alignItems: "center",
}));

interface Props {
  study: StudyMetadata;
  parentStudy?: StudyMetadata;
  variantNb: number;
}

function Details({ study, parentStudy, variantNb }: Props) {
  const [t, i18n] = useTranslation();
  const publicModeLabel =
    PUBLIC_MODE_LIST.find((mode) => mode.id === study?.publicMode)?.name || "";

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "flex-start",
        alignItems: "center",
        gap: 2,
      }}
    >
      <Item>
        <ScheduleOutlinedIcon fontSize="inherit" sx={{ color: "text.secondary" }} />
        <TinyText>{convertUTCToLocalTime(study.creationDate)}</TinyText>
      </Item>
      <Item>
        <UpdateOutlinedIcon fontSize="inherit" sx={{ color: "text.secondary" }} />
        <TinyText>{buildModificationDate(study.modificationDate, t, i18n.language)}</TinyText>
      </Item>
      <StyledDivider />
      <TinyText>{`v${compactSemanticVersion(study.version)}`}</TinyText>
      <StyledDivider />
      {parentStudy && (
        <Item>
          <AltRouteOutlinedIcon fontSize="inherit" sx={{ color: "text.secondary" }} />
          <Tooltip title={parentStudy.name}>
            <RouterLink
              to="/studies/$studyId"
              params={{ studyId: parentStudy.id }}
              color="text.secondary"
              fontSize={12}
              sx={truncateTextSx(200)}
            >
              {parentStudy.name}
            </RouterLink>
          </Tooltip>
        </Item>
      )}
      <Item>
        <AccountTreeOutlinedIcon fontSize="inherit" sx={{ color: "text.secondary" }} />
        <TinyText>{variantNb}</TinyText>
      </Item>
      <StyledDivider />
      <Item>
        <EditorIcon />
        <TinyText>{study.editor}</TinyText>
      </Item>
      <Item>
        <SecurityOutlinedIcon fontSize="inherit" sx={{ color: "text.secondary" }} />
        <TinyText>{t(publicModeLabel)}</TinyText>
      </Item>
    </Box>
  );
}

export default Details;
