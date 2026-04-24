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

import CopyButton from "@/components/buttons/CopyButton";
import type { StudyMetadata } from "@/types/types";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import { Box, Button, Checkbox, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";
import FavoriteStudyToggle from "../../../../../-shared/components/studies/FavoriteToggle/FavoriteStudyToggle";

interface Props {
  studyId: StudyMetadata["id"];
  isSelected: boolean;
  /** When true the checkbox is always visible, when false it hides until the card is hovered. */
  hasStudiesSelected: boolean;
  onSelectionChange: () => void;
  onCopyId: () => void;
  onMenuOpen: (event: React.MouseEvent<HTMLButtonElement>) => void;
}

function StudyCardActions({
  studyId,
  isSelected,
  hasStudiesSelected,
  onSelectionChange,
  onCopyId,
  onMenuOpen,
}: Props) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ display: "flex", flexShrink: 0, alignItems: "center" }}>
      <Checkbox
        checked={isSelected}
        size="small"
        sx={[
          !hasStudiesSelected && {
            ".StudyCard:not(:hover) &": { visibility: "hidden" },
          },
        ]}
        onChange={onSelectionChange}
      />
      <FavoriteStudyToggle studyId={studyId} />
      <CopyButton tooltip={t("study.copyId")} onClick={onCopyId} />
      <Tooltip title={t("studies.moreActions")}>
        <Button variant="outlined" onClick={onMenuOpen} sx={{ px: 0, minWidth: 0 }}>
          <MoreVertIcon />
        </Button>
      </Tooltip>
    </Box>
  );
}

export default StudyCardActions;
