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

import FormDialog from "@/components/dialogs/FormDialog";
import CheckBoxFE from "@/components/fieldEditors/CheckBoxFE";
import Fieldset from "@/components/Fieldset";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import StudyPathFE from "@/routes/-shared/components/studies/StudyPathFE";
import { createOrReplaceUserResource } from "@/services/api/studies/userResources";
import type { StudyMetadata } from "@/types/types";
import CreateNewFolderIcon from "@mui/icons-material/CreateNewFolder";
import { useNavigate } from "@tanstack/react-router";
import { useContext } from "react";
import { useTranslation } from "react-i18next";
import UserResourcesContext from "../../UserResourcesContext";

interface Props {
  open: boolean;
  onCancel: VoidFunction;
  studyId: StudyMetadata["id"];
  currentPath: string;
}

const defaultValues = { folder: "", openFolder: false };

type DefaultValues = typeof defaultValues;

function CreateFolderDialog({ open, onCancel, studyId, currentPath }: Props) {
  const { reloadTree } = useContext(UserResourcesContext);
  const { t } = useTranslation();
  const navigate = useNavigate();

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const toPath = (folder: string) => (currentPath ? `${currentPath}/${folder}` : folder);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values: { folder } }: SubmitHandlerPlus<DefaultValues>) => {
    return createOrReplaceUserResource({ studyId, path: toPath(folder), resourceType: "folder" });
  };

  const handleSubmitSuccessful = async ({
    values: { folder, openFolder },
  }: SubmitHandlerPlus<DefaultValues>) => {
    onCancel();

    await reloadTree();

    if (openFolder) {
      navigate({
        to: "/studies/$studyId/explore/user-resources",
        params: { studyId },
        search: { path: toPath(folder) },
      });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open={open}
      title={t("study.fileExplorer.folder.new")}
      titleIcon={CreateNewFolderIcon}
      config={{ defaultValues }}
      onCancel={onCancel}
      submitButtonText={t("global.create")}
      submitButtonIcon={null}
      onSubmit={handleSubmit}
      onSubmitSuccessful={handleSubmitSuccessful}
    >
      {({ control }) => (
        <Fieldset fullFieldWidth>
          <StudyPathFE
            name="folder"
            control={control}
            rules={{ required: t("form.field.required") }}
            helperText={t("study.fileExplorer.folder.new.name.helper")}
            disableAdornment
          />
          <CheckBoxFE
            label={t("study.fileExplorer.folder.new.openDirectory")}
            name="openFolder"
            control={control}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CreateFolderDialog;
