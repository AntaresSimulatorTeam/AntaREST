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

import CustomScrollbar from "@/components/CustomScrollbar";
import EditorIcon from "@/components/icons/EditorIcon";
import RouterLink from "@/components/router/RouterLink";
import { PUBLIC_MODE_LIST } from "@/components/utils/constants";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getParentStudy } from "@/redux/selectors";
import type { VariantTree } from "@/services/api/studies/variants/types";
import { buildModificationDate, convertUTCToLocalTime, getDescendantCount } from "@/services/utils";
import { truncateTextSx } from "@/utils/muiUtils";
import { compactSemanticVersion } from "@/utils/versionUtils";
import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import AltRouteOutlinedIcon from "@mui/icons-material/AltRouteOutlined";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";
import SecurityOutlinedIcon from "@mui/icons-material/SecurityOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import { Chip, Divider, Stack, Tooltip, Typography, styled } from "@mui/material";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";
import useStudy from "../../-hooks/useStudy";
import useStudyVariantTree from "../../-hooks/useStudyVariantTree";

const TinyText = styled(Typography)(({ theme }) => ({
  fontSize: 12,
  color: theme.vars.palette.text.secondary,
}));

function Details() {
  const study = useStudy();
  const [t, i18n] = useTranslation();
  const parentStudy = useAppSelector((state) => getParentStudy(state, study.id));

  const selectDescendantCount = useCallback(
    (variantTree: VariantTree) => getDescendantCount(variantTree, study.id),
    [study.id],
  );

  const { data: descendantCount } = useStudyVariantTree({
    studyId: study.id,
    select: selectDescendantCount,
  });

  const publicModeLabel =
    PUBLIC_MODE_LIST.find((mode) => mode.id === study?.publicMode)?.name || "";

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const tooltipContent = (
    <Stack direction="column">
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
      <Stack>
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
    <Stack
      spacing={1.5}
      divider={<Divider orientation="vertical" flexItem />}
      sx={{ overflow: "auto" }}
    >
      <Tooltip title={tooltipContent} placement="bottom-start">
        <InfoOutlinedIcon fontSize="small" sx={{ color: "text.secondary", cursor: "pointer" }} />
      </Tooltip>
      <TinyText>{`v${compactSemanticVersion(study.version)}`}</TinyText>
      <Stack spacing={1}>
        <AccountTreeOutlinedIcon fontSize="inherit" sx={{ color: "text.secondary" }} />
        <TinyText>{descendantCount}</TinyText>
      </Stack>
      <CustomScrollbar>
        <Stack spacing={1}>
          {study.managed ? (
            <Chip label={t("study.managedStudy")} color="info" />
          ) : (
            <Chip label={study.workspace} />
          )}
          {study.tags?.map((tag) => <Chip key={tag} label={tag} />)}
        </Stack>
      </CustomScrollbar>
    </Stack>
  );
}

export default Details;
