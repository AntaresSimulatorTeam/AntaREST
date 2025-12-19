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

import EditorIcon from "@/components/common/icons/EditorIcon";
import { compactSemanticVersion } from "@/utils/versionUtils";
import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import AltRouteOutlinedIcon from "@mui/icons-material/AltRouteOutlined";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";
import SecurityOutlinedIcon from "@mui/icons-material/SecurityOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import { Box, Divider, Tooltip, Typography, styled } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { buildModificationDate, convertUTCToLocalTime } from "../../../../services/utils";
import type { StudyMetadata } from "../../../../types/types";
import { PUBLIC_MODE_LIST } from "../../../common/utils/constants";

const MAX_STUDY_TITLE_LENGTH = 45;

const TinyText = styled(Typography)(({ theme }) => ({
  fontSize: 12,
  color: theme.palette.text.secondary,
}));

const LinkText = styled(Link)(({ theme }) => ({
  fontSize: 12,
  color: theme.palette.secondary.main,
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

  const tooltipContent = (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
      <Item>
        <ScheduleOutlinedIcon />
        <TinyText>{convertUTCToLocalTime(study.creationDate)}</TinyText>
      </Item>
      <Item>
        <UpdateOutlinedIcon />
        <TinyText>{buildModificationDate(study.modificationDate, t, i18n.language)}</TinyText>
      </Item>
      {parentStudy && (
        <Item>
          <AltRouteOutlinedIcon />
          <LinkText to={`/studies/${parentStudy.id}`}>
            {`${parentStudy.name.substring(0, MAX_STUDY_TITLE_LENGTH)}...`}
          </LinkText>
        </Item>
      )}
      <Item>
        <EditorIcon />
        <TinyText>{study.editor}</TinyText>
      </Item>
      <Item>
        <SecurityOutlinedIcon />
        <TinyText>{t(publicModeLabel)}</TinyText>
      </Item>
    </Box>
  );

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "flex-start",
        alignItems: "center",
        gap: 1,
      }}
    >
      <Tooltip title={tooltipContent} placement="bottom-start">
        <InfoOutlinedIcon fontSize="small" sx={{ color: "text.secondary", cursor: "pointer" }} />
      </Tooltip>
      <StyledDivider />
      <TinyText>{`v${compactSemanticVersion(study.version)}`}</TinyText>
      <StyledDivider />
      <Item>
        <AccountTreeOutlinedIcon fontSize="inherit" sx={{ color: "text.secondary" }} />
        <TinyText>{variantNb}</TinyText>
      </Item>
    </Box>
  );
}

export default Details;
