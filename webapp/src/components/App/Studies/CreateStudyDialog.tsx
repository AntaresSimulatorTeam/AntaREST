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

import SelectFE from "@/components/common/fieldEditors/SelectFE";
import { validateStudyName } from "@/utils/studiesUtils";
import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
import { Button, IconButton } from "@mui/material";
import { useSnackbar } from "notistack";
import * as R from "ramda";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { createStudy } from "../../../redux/ducks/studies";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { getGroups, getStudyVersionsFormatted } from "../../../redux/selectors";
import type { StudyMetadata, StudyPublicMode } from "../../../types/types";
import FormDialog from "../../common/dialogs/FormDialog";
import CheckboxesTagsFE from "../../common/fieldEditors/CheckboxesTagsFE";
import StringFE from "../../common/fieldEditors/StringFE";
import Fieldset from "../../common/Fieldset";
import type { SubmitHandlerPlus } from "../../common/Form/types";
import { PUBLIC_MODE_LIST } from "../../common/utils/constants";

interface FieldValues {
  name: string;
  version: string;
  publicMode: StudyPublicMode;
  groups: string[];
  tags: string[];
}

interface Props {
  open: boolean;
  onClose: VoidFunction;
}

function CreateStudyDialog({ open, onClose }: Props) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { enqueueSnackbar, closeSnackbar } = useSnackbar();
  const versionList = useAppSelector(getStudyVersionsFormatted);
  const groupList = useAppSelector(getGroups);
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values: { name, ...rest } }: SubmitHandlerPlus<FieldValues>) => {
    return dispatch(
      createStudy({
        name: name.trim(),
        ...rest,
      }),
    ).unwrap();
  };

  const handleSubmitSuccessful = (
    { values: { name } }: SubmitHandlerPlus<FieldValues>,
    newStudy: StudyMetadata,
  ) => {
    const snackbarId = enqueueSnackbar(t("studies.success.createStudy", { name }), {
      variant: "success",
      preventDuplicate: false,
      action: (
        <>
          <Button
            onClick={() => {
              navigate(`/studies/${newStudy.id}`);
              closeSnackbar(snackbarId);
            }}
          >
            {t("button.explore")}
          </Button>
          <IconButton onClick={() => closeSnackbar(snackbarId)}>
            <CloseRoundedIcon />
          </IconButton>
        </>
      ),
    });

    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("studies.createNewStudy")}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      onSubmitSuccessful={handleSubmitSuccessful}
      config={{
        defaultValues: {
          name: "",
          version: R.last(versionList)?.id.toString(),
          publicMode: "NONE",
          groups: [],
          tags: [],
        },
      }}
    >
      {({ control }) => (
        <>
          <Fieldset fullFieldWidth>
            <StringFE
              label={t("studies.studyName")}
              name="name"
              control={control}
              rules={{ validate: validateStudyName }}
            />
            <SelectFE
              label={t("global.version")}
              options={versionList.map((ver) => ({
                label: ver.name,
                value: ver.id,
              }))}
              name="version"
              control={control}
            />
          </Fieldset>
          <Fieldset legend={t("global.permission")} fullFieldWidth>
            <SelectFE
              label={t("study.publicMode")}
              options={PUBLIC_MODE_LIST.map((mode) => ({
                label: t(mode.name),
                value: mode.id,
              }))}
              name="publicMode"
              control={control}
            />
            <SelectFE
              label={t("global.group")}
              options={groupList.map((group) => group.name)}
              name="groups"
              control={control}
              multiple
            />
          </Fieldset>
          <Fieldset legend="Metadata" fullFieldWidth>
            <CheckboxesTagsFE
              options={[]}
              label={t("studies.enterTag")}
              freeSolo
              name="tags"
              control={control}
            />
          </Fieldset>
        </>
      )}
    </FormDialog>
  );
}

export default CreateStudyDialog;
