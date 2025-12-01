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
import type { AxiosError } from "axios";
import debug from "debug";
import { useSnackbar } from "notistack";
import * as R from "ramda";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "../../../../../hooks/usePromiseWithSnackbarError";
import { updateStudy } from "../../../../../redux/ducks/studies";
import useAppDispatch from "../../../../../redux/hooks/useAppDispatch";
import {
  addStudyGroup,
  changePublicMode,
  deleteStudyGroup,
  updateStudyMetadata,
} from "../../../../../services/api/study";
import { getGroups } from "../../../../../services/api/user";
import type { StudyMetadata } from "../../../../../types/types";
import FormDialog from "../../../../common/dialogs/FormDialog";
import CheckboxesTagsFE from "../../../../common/fieldEditors/CheckboxesTagsFE";
import StringFE from "../../../../common/fieldEditors/StringFE";
import Fieldset from "../../../../common/Fieldset";
import type { SubmitHandlerPlus } from "../../../../common/Form/types";
import { PUBLIC_MODE_LIST } from "../../../../common/utils/constants";

const logErr = debug("antares:createstudyform:error");

interface Props {
  open: boolean;
  onClose: () => void;
  study: StudyMetadata;
}

function UpdateStudyDialog({ open, onClose, study }: Props) {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const dispatch = useAppDispatch();

  const { data: groupList = [] } = usePromiseWithSnackbarError(getGroups, {
    errorMessage: t("settings.error.groupsError"),
  });

  const defaultValues = useMemo(
    () => ({
      name: study.name,
      publicMode: study.publicMode,
      groups: study.groups.map((group) => group.id),
      tags: study.tags ? study.tags : [],
    }),
    [study],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus<typeof defaultValues>) => {
    const { name, tags, groups, publicMode } = data.dirtyValues;
    const { id: studyId } = study;

    try {
      // TODO create redux thunk

      // Update metadata
      if (name || tags) {
        await updateStudyMetadata(studyId, {
          name: data.values.name.trim(),
          tags: data.values.tags,
        });
      }

      // Update public mode
      if (publicMode) {
        await changePublicMode(studyId, publicMode);
      }

      // Update group
      if (groups) {
        const toDelete = R.difference(defaultValues.groups, groups);
        const toAdd = R.difference(groups, defaultValues.groups);

        await Promise.all(toDelete.map((id) => deleteStudyGroup(studyId, id as string)));

        await Promise.all(toAdd.map((id) => addStudyGroup(studyId, id as string)));
      }

      dispatch(
        updateStudy({
          id: study.id,
          changes: {
            name: data.values.name.trim(),
            tags: data.values.tags,
          },
        }),
      );

      enqueueSnackbar(t("studies.success.saveData"), {
        variant: "success",
      });
    } catch (e) {
      logErr("Failed to create new study", name, e);
      enqueueErrorSnackbar(t("studies.error.saveData"), e as AxiosError);
    }

    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("study.properties")}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      config={{ defaultValues }}
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
              options={groupList.map((group) => ({
                label: group.name,
                value: group.id,
              }))}
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

export default UpdateStudyDialog;
