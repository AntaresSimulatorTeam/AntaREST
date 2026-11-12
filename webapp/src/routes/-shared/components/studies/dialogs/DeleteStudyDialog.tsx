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

import ConfirmationDialog from "@/components/dialogs/ConfirmationDialog";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { deleteStudy } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import type { Study } from "@/services/api/studies/types";
import type { StudyMetadata } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import { Typography } from "@mui/material";
import { useMatch, useNavigate } from "@tanstack/react-router";
import { Trans, useTranslation } from "react-i18next";

interface Props {
  study: StudyMetadata;
  /**
   * @see StudyActionsMenuProps.studyInfo for more details on how this prop is derived.
   */
  studyInfo?: {
    parentStudy?: Study;
    descendantCount?: number;
  };
  open: boolean;
  onClose: VoidFunction;
}

function DeleteStudyDialog({ study, studyInfo, open, onClose }: Props) {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const isStudyRoute = !!useMatch({ from: "/_authenticated/studies/$studyId", shouldThrow: false });
  const { parentStudy, descendantCount } = studyInfo ?? {};

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleConfirm = async () => {
    try {
      await dispatch(deleteStudy({ id: study.id, deleteChildren: true })).unwrap();

      onClose();

      if (isStudyRoute) {
        navigate(
          parentStudy
            ? { to: "/studies/$studyId", params: { studyId: parentStudy.id } }
            : { to: "/studies" },
        );
      }
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
        {typeof descendantCount !== "number" || descendantCount > 0 ? (
          <Trans
            t={t}
            i18nKey="studies.question.deleteWithVariants"
            values={{ descendantCount, studyName: study.name }}
          />
        ) : (
          t("studies.question.delete", { studyName: study.name })
        )}
      </Typography>
    </ConfirmationDialog>
  );
}

export default DeleteStudyDialog;
