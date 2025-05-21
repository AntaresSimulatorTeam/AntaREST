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

import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import AltRouteOutlinedIcon from "@mui/icons-material/AltRouteOutlined";
import PersonOutlineOutlinedIcon from "@mui/icons-material/PersonOutlineOutlined";
import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";
import SecurityOutlinedIcon from "@mui/icons-material/SecurityOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import { Box, Divider, Tooltip, Typography, styled } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import {
  buildModificationDate,
  convertUTCToLocalTime,
  displayVersionName,
} from "../../../../services/utils";
import type { StudyMetadata } from "../../../../types/types";
import { PUBLIC_MODE_LIST } from "../../../common/utils/constants";

const MAX_STUDY_TITLE_LENGTH = 45;

const TinyText = styled(Typography)(({ theme }) => ({
  fontSize: "14px",
  color: theme.palette.text.secondary,
}));

const LinkText = styled(Link)(({ theme }) => ({
  fontSize: "14px",
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
}));

interface Props {
  study: StudyMetadata;
  parentStudy?: StudyMetadata;
  variantNb?: number;
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
        <ScheduleOutlinedIcon sx={{ color: "text.secondary" }} />
        <TinyText>{convertUTCToLocalTime(study.creationDate)}</TinyText>
      </Item>
      <Item>
        <UpdateOutlinedIcon sx={{ color: "text.secondary" }} />
        <TinyText>{buildModificationDate(study.modificationDate, t, i18n.language)}</TinyText>
      </Item>
      <StyledDivider />
      <TinyText>{`v${displayVersionName(study.version)}`}</TinyText>
      {parentStudy && (
        <Item>
          <AltRouteOutlinedIcon sx={{ color: "text.secondary" }} />
          <Tooltip title={parentStudy.name}>
            <LinkText to={`/studies/${parentStudy.id}`}>
              {`${parentStudy.name.substring(0, MAX_STUDY_TITLE_LENGTH)}...`}
            </LinkText>
          </Tooltip>
        </Item>
      )}
      <Item>
        <AccountTreeOutlinedIcon sx={{ color: "text.secondary" }} />
        <TinyText>{variantNb}</TinyText>
      </Item>
      <StyledDivider />
      <Item>
        <PersonOutlineOutlinedIcon sx={{ color: "text.secondary" }} />
        <TinyText>{study.owner.name}</TinyText>
      </Item>
      <Item>
        <SecurityOutlinedIcon sx={{ color: "text.secondary" }} />
        <TinyText>{t(publicModeLabel)}</TinyText>
      </Item>
    </Box>
  );
}

export default Details;
