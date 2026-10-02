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

import type { StudyMetadata } from "@/types/types";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import ArchiveOutlinedIcon from "@mui/icons-material/ArchiveOutlined";
import StorageIcon from "@mui/icons-material/Storage";
import { Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";
import { studyTypeIconSx } from "./styles";

interface Props {
  study: StudyMetadata;
}

function StudyTypeIcon({ study }: Props) {
  const { t } = useTranslation();

  if (study.archived && study.managed) {
    return (
      <Tooltip title={t("studies.archived")}>
        <ArchiveOutlinedIcon sx={{ ...studyTypeIconSx, color: "warning.main" }} />
      </Tooltip>
    );
  }

  if (study.managed) {
    return (
      <Tooltip title={t("studies.managedStudy")}>
        <AccountTreeIcon sx={{ ...studyTypeIconSx, color: "info.main" }} />
      </Tooltip>
    );
  }

  return (
    <Tooltip title={study.workspace}>
      <StorageIcon sx={{ ...studyTypeIconSx, color: "text.secondary" }} />
    </Tooltip>
  );
}

export default StudyTypeIcon;
