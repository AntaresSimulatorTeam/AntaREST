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
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";
import SecurityOutlinedIcon from "@mui/icons-material/SecurityOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import { Divider, Stack, Tooltip, Typography, styled } from "@mui/material";
import { useTranslation } from "react-i18next";

const TinyText = styled(Typography)(({ theme }) => ({
  fontSize: 12,
  color: theme.palette.text.secondary,
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
    <Stack direction="column" spacing={1}>
      <Stack spacing={1}>
        <ScheduleOutlinedIcon />
        <TinyText>{convertUTCToLocalTime(study.creationDate)}</TinyText>
      </Stack>
      <Stack spacing={1}>
        <UpdateOutlinedIcon />
        <TinyText>{buildModificationDate(study.modificationDate, t, i18n.language)}</TinyText>
      </Stack>
      {parentStudy && (
        <Stack spacing={1}>
          <AltRouteOutlinedIcon />
          <RouterLink
            to="/studies/$studyId"
            params={{ studyId: parentStudy.id }}
            color="text.secondary"
            fontSize={12}
            sx={truncateTextSx(200)}
          >
            {parentStudy.name}
          </RouterLink>
        </Stack>
      )}
      <Stack spacing={1}>
        <EditorIcon />
        <TinyText>{study.editor}</TinyText>
      </Stack>
      <Stack spacing={1}>
        <SecurityOutlinedIcon />
        <TinyText>{t(publicModeLabel)}</TinyText>
      </Stack>
    </Stack>
  );

  return (
    <Stack spacing={2} divider={<Divider orientation="vertical" flexItem />}>
      <Tooltip title={tooltipContent} placement="bottom-start">
        <InfoOutlinedIcon fontSize="small" sx={{ color: "text.secondary", cursor: "pointer" }} />
      </Tooltip>
      <TinyText>{`v${compactSemanticVersion(study.version)}`}</TinyText>
      <Stack spacing={1}>
        <AccountTreeOutlinedIcon fontSize="inherit" sx={{ color: "text.secondary" }} />
        <TinyText>{variantNb}</TinyText>
      </Stack>
    </Stack>
  );
}

export default Details;
