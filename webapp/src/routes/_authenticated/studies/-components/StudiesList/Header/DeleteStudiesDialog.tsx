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
import { useState } from "react";
import { useTranslation } from "react-i18next";
import ConfirmationDialog from "@/components/dialogs/ConfirmationDialog";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { deleteStudies } from "@/services/api/study";
import type { StudyMetadata } from "@/types/types";
import { toError } from "@/utils/fnUtils";

interface Props {
  studyIds: Array<StudyMetadata["id"]>;
  open: boolean;
  onClose: VoidFunction;
}

function DeleteStudiesDialog({ studyIds, open, onClose }: Props) {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();
  const [isDeleting, setIsDeleting] = useState(false);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleConfirm = async () => {
    setIsDeleting(true);
    try {
      await deleteStudies(studyIds, true);

      onClose();
    } catch (err) {
      enqueueErrorSnackbar(t("studies.error.deleteStudies"), toError(err));
    } finally {
      setIsDeleting(false);
    }
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
      disableConfirm={isDeleting}
    >
      <Typography>{t("studies.question.deleteMultiple", { count: studyIds.length })}</Typography>
    </ConfirmationDialog>
  );
}

export default DeleteStudiesDialog;
