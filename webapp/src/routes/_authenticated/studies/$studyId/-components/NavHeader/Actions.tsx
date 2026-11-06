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

import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import FavoriteStudyToggle from "@/routes/-shared/components/studies/FavoriteToggle/FavoriteStudyToggle";
import StudyActionsMenu from "@/routes/-shared/components/studies/StudyActionsMenu";
import { toError } from "@/utils/fnUtils";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import HistoryOutlinedIcon from "@mui/icons-material/HistoryOutlined";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import { Button, Divider, IconButton, Stack, Tooltip } from "@mui/material";
import { enqueueSnackbar } from "notistack";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import useStudy from "../../-hooks/useStudy";
import useStudyInfo from "../../-hooks/useStudyInfo";
import CommandsDrawer from "./CommandsDrawer";

export type DialogType = "commands";

function Actions() {
  const study = useStudy();
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [openDialog, setOpenDialog] = useState<DialogType | null>(null);
  const { data: studyInfo } = useStudyInfo({ studyId: study.id });

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const closeDialog = () => setOpenDialog(null);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleCopyId = async () => {
    try {
      await navigator.clipboard.writeText(study.id);
      enqueueSnackbar(t("study.success.studyIdCopy"), {
        variant: "success",
      });
    } catch (err) {
      enqueueErrorSnackbar(t("study.error.studyIdCopy"), toError(err));
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Stack spacing={1}>
        <FavoriteStudyToggle studyId={study.id} />
        <Tooltip title={t("study.copyId")}>
          <IconButton onClick={handleCopyId}>
            <ContentCopyIcon />
          </IconButton>
        </Tooltip>
        <Divider flexItem orientation="vertical" />
        {studyInfo.isVariant && (
          <IconButton color="primary" onClick={() => setOpenDialog("commands")}>
            <HistoryOutlinedIcon />
          </IconButton>
        )}
        <Button
          variant="outlined"
          onClick={(event) => setAnchorEl(event.currentTarget)}
          sx={{ px: 0 }}
        >
          <MoreVertIcon />
        </Button>
      </Stack>
      <StudyActionsMenu
        open={!!anchorEl}
        anchorEl={anchorEl}
        study={study}
        studyInfo={studyInfo}
        onClose={() => setAnchorEl(null)}
      />
      <CommandsDrawer open={openDialog === "commands"} studyId={study.id} onClose={closeDialog} />
    </>
  );
}

export default Actions;
