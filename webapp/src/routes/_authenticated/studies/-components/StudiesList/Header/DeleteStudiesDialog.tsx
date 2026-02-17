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

import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import { Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import ConfirmationDialog from "@/components/dialogs/ConfirmationDialog";
import type { StudyMetadata } from "@/types/types";
import { useDeleteStudies } from "./useDeleteStudies";

interface Props {
  studyIds: Array<StudyMetadata["id"]>;
  open: boolean;
  onClose: VoidFunction;
}

function DeleteStudiesDialog({ studyIds, open, onClose }: Props) {
  const { t } = useTranslation();
  const deleteStudies = useDeleteStudies({ onSuccess: onClose });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleConfirm = () => {
    deleteStudies.mutate({ studyIds });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ConfirmationDialog
      open={open}
      titleIcon={DeleteOutlinedIcon}
      alert="error"
      maxWidth="xs"
      onConfirm={handleConfirm}
      onCancel={onClose}
      disableConfirm={deleteStudies.isPending}
    >
      <Typography>{t("studies.question.deleteMany", { count: studyIds.length })}</Typography>
    </ConfirmationDialog>
  );
}

export default DeleteStudiesDialog;
