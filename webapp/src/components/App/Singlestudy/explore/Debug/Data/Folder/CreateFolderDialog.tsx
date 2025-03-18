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

import FormDialog from "@/components/common/dialogs/FormDialog";
import CheckBoxFE from "@/components/common/fieldEditors/CheckBoxFE";
import StringFE from "@/components/common/fieldEditors/StringFE";
import Fieldset from "@/components/common/Fieldset";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import { createFolder } from "@/services/api/studies/raw";
import type { StudyMetadata } from "@/types/types";
import { validatePath } from "@/utils/validation/string";
import CreateNewFolderIcon from "@mui/icons-material/CreateNewFolder";
import { useContext } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";
import DebugContext from "../../DebugContext";

interface Props {
  open: boolean;
  onCancel: VoidFunction;
  studyId: StudyMetadata["id"];
  parentPath: string;
}

const defaultValues = { folder: "", openFolder: false };

type DefaultValues = typeof defaultValues;

function CreateFolderDialog({ open, onCancel, studyId, parentPath }: Props) {
  const { reloadTree } = useContext(DebugContext);
  const { t } = useTranslation();
  const setSearchParams = useSearchParams()[1];

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const toPath = (directory: string) => `${parentPath}/${directory}`;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values: { folder } }: SubmitHandlerPlus<DefaultValues>) => {
    return createFolder({ studyId, path: toPath(folder) });
  };

  const handleSubmitSuccessful = async ({
    values: { folder, openFolder },
  }: SubmitHandlerPlus<DefaultValues>) => {
    onCancel();

    await reloadTree();

    if (openFolder) {
      setSearchParams({ path: toPath(folder) });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open={open}
      title={t("study.debug.folder.new")}
      titleIcon={CreateNewFolderIcon}
      config={{ defaultValues }}
      onCancel={onCancel}
      submitButtonText={t("global.create")}
      submitButtonIcon={null}
      cancelButtonText={t("global.cancel")}
      onSubmit={handleSubmit}
      onSubmitSuccessful={handleSubmitSuccessful}
    >
      {({ control }) => (
        <Fieldset fullFieldWidth>
          <StringFE
            label={t("global.name")}
            helperText={t("study.debug.folder.new.name.helper")}
            name="folder"
            control={control}
            rules={{
              validate: validatePath({ allowToStartWithSlash: false, allowToEndWithSlash: false }),
            }}
          />
          <CheckBoxFE
            label={t("study.debug.folder.new.openDirectory")}
            name="openFolder"
            control={control}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CreateFolderDialog;
