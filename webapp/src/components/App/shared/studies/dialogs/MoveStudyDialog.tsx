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

import DriveFileMoveIcon from "@mui/icons-material/DriveFileMove";
import { type DialogProps } from "@mui/material";
import { useSnackbar } from "notistack";
import * as R from "ramda";
import { useTranslation } from "react-i18next";
import { moveStudy } from "../../../../../services/api/study";
import type { StudyMetadata } from "../../../../../types/types";
import FormDialog from "../../../../common/dialogs/FormDialog";
import type { SubmitHandlerPlus } from "../../../../common/Form/types";
import StudyPathFE from "../StudyPathFE";

function formalizePath(path: string | undefined, studyId?: StudyMetadata["id"]) {
  const trimmedPath = path?.trim();

  if (!trimmedPath) {
    return "";
  }

  const pathArray = trimmedPath.split("/").filter(Boolean);

  if (studyId) {
    const lastFolder = R.last(pathArray);

    // The API automatically add the study ID to a not empty path when moving a study.
    // So we need to remove it from the display path.
    if (lastFolder === studyId) {
      return pathArray.slice(0, -1).join("/");
    }
  }

  return pathArray.join("/");
}

interface Props extends DialogProps {
  study: StudyMetadata;
  onClose: () => void;
}

function MoveStudyDialog(props: Props) {
  const { study, open, onClose } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();

  const defaultValues = {
    path: formalizePath(study.folder, study.id),
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    const path = formalizePath(data.values.path);
    return moveStudy(study.id, path);
  };

  const handleSubmitSuccessful = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    onClose();

    enqueueSnackbar(
      t("studies.success.moveStudy", {
        study: study.name,
        path: data.values.path || "/", // Empty path move the study to the root
      }),
      {
        variant: "success",
      },
    );
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open={open}
      title={t("global.move")}
      titleIcon={DriveFileMoveIcon}
      config={{ defaultValues }}
      onSubmit={handleSubmit}
      onSubmitSuccessful={handleSubmitSuccessful}
      onCancel={onClose}
      submitButtonIcon={null}
      submitButtonText={t("global.move")}
    >
      {({ control }) => (
        <StudyPathFE name="path" control={control} margin="dense" fullWidth autoFocus />
      )}
    </FormDialog>
  );
}

export default MoveStudyDialog;
