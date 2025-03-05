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

import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import AltRouteOutlinedIcon from "@mui/icons-material/AltRouteOutlined";
import SecurityOutlinedIcon from "@mui/icons-material/SecurityOutlined";
import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import PersonOutlineOutlinedIcon from "@mui/icons-material/PersonOutlineOutlined";
import { Box, Divider, Tooltip, Typography, styled } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import {
  buildModificationDate,
  convertUTCToLocalTime,
  countDescendants,
  displayVersionName,
} from "../../../../services/utils";
import type { StudyMetadata, VariantTree } from "../../../../types/types";
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
  study: StudyMetadata | undefined;
  parent: StudyMetadata | undefined;
  childrenTree: VariantTree | undefined;
}

function Details({ study, parent, childrenTree }: Props) {
  const [t, i18n] = useTranslation();
  const publicModeLabel =
    PUBLIC_MODE_LIST.find((mode) => mode.id === study?.publicMode)?.name || "";

  if (!study) {
    return null;
  }

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
      {parent && (
        <Item>
          <AltRouteOutlinedIcon sx={{ color: "text.secondary" }} />
          <Tooltip title={parent.name}>
            <LinkText to={`/studies/${parent.id}`}>
              {`${parent.name.substring(0, MAX_STUDY_TITLE_LENGTH)}...`}
            </LinkText>
          </Tooltip>
        </Item>
      )}
      {childrenTree && (
        <Item>
          <AccountTreeOutlinedIcon sx={{ color: "text.secondary" }} />
          <TinyText>{countDescendants(childrenTree)}</TinyText>
        </Item>
      )}
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
