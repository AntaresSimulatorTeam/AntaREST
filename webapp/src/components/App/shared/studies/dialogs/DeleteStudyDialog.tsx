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

import ConfirmationDialog from "@/components/common/dialogs/ConfirmationDialog";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { deleteStudy } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import type { StudyMetadata } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import { Typography } from "@mui/material";
import { t } from "i18next";
import { Trans } from "react-i18next";

import { useNavigate } from "react-router";

interface Props {
  study: StudyMetadata;
  parentStudy?: StudyMetadata;
  variantNb?: number;
  open: boolean;
  onClose: VoidFunction;
}

function DeleteStudyDialog({ study, parentStudy, variantNb, open, onClose }: Props) {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleConfirm = async () => {
    try {
      await dispatch(deleteStudy({ id: study.id, deleteChildren: true })).unwrap();

      navigate(parentStudy ? `/studies/${parentStudy.id}` : "/studies");

      onClose();
    } catch (err) {
      enqueueErrorSnackbar(t("studies.error.deleteStudy"), toError(err));
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
    >
      <Typography>
        {typeof variantNb !== "number" || variantNb > 0 ? (
          <Trans t={t} i18nKey="studies.question.deleteWithVariants" values={{ variantNb }} />
        ) : (
          t("studies.question.delete")
        )}
      </Typography>
    </ConfirmationDialog>
  );
}

export default DeleteStudyDialog;
