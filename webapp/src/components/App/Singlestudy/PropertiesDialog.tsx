/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useMemo } from "react";
import { AxiosError } from "axios";
import debug from "debug";
import { useSnackbar } from "notistack";
import * as R from "ramda";
import { useTranslation } from "react-i18next";

import { StudyMetadata } from "@/common/types";
import FormDialog from "@/components/common/dialogs/FormDialog";
import CheckboxesTagsFE from "@/components/common/fieldEditors/CheckboxesTagsFE";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import StringFE from "@/components/common/fieldEditors/StringFE";
import Fieldset from "@/components/common/Fieldset";
import { SubmitHandlerPlus } from "@/components/common/Form/types";
import { PUBLIC_MODE_LIST } from "@/components/common/utils/constants";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import { updateStudy } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import {
  addStudyGroup,
  changePublicMode,
  deleteStudyGroup,
  updateStudyMetadata,
} from "@/services/api/study";
import { getGroups } from "@/services/api/user";
import { validateString } from "@/utils/validation/string";

const logErr = debug("antares:createstudyform:error");

interface Props {
  open: boolean;
  onClose: () => void;
  study: StudyMetadata;
  updateStudyData?: VoidFunction;
}

function PropertiesDialog(props: Props) {
  const [t] = useTranslation();
  const { open, onClose, study, updateStudyData } = props;
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

  const handleSubmit = async (
    data: SubmitHandlerPlus<typeof defaultValues>,
  ) => {
    const { name, tags, groups, publicMode } = data.dirtyValues;
    const { id: studyId } = study;

    try {
      // TODO create redux thunk

      // Update metadata
      if (name || tags) {
        await updateStudyMetadata(studyId, {
          name: data.values.name,
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

        await Promise.all(
          toDelete.map((id) => deleteStudyGroup(studyId, id as string)),
        );

        await Promise.all(
          toAdd.map((id) => addStudyGroup(studyId, id as string)),
        );
      }

      if (updateStudyData) {
        updateStudyData();
      } else {
        dispatch(
          updateStudy({
            id: study.id,
            changes: {
              name: data.values.name,
              tags: data.values.tags,
            },
          }),
        );
      }

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
          <StringFE
            label={t("studies.studyName")}
            name="name"
            control={control}
            rules={{ validate: (v) => validateString(v) }}
            sx={{ mx: 0 }}
            fullWidth
          />

          <Fieldset legend={t("global.permission")} fullFieldWidth>
            <SelectFE
              label={t("study.publicMode")}
              options={PUBLIC_MODE_LIST.map((mode) => ({
                label: t(mode.name),
                value: mode.id,
              }))}
              name="publicMode"
              control={control}
              fullWidth
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
              fullWidth
            />
          </Fieldset>

          <Fieldset legend="Metadata" fullFieldWidth>
            <CheckboxesTagsFE
              options={[]}
              label={t("studies.enterTag")}
              freeSolo
              fullWidth
              sx={{ px: 0 }}
              name="tags"
              control={control}
            />
          </Fieldset>
        </>
      )}
    </FormDialog>
  );
}

export default PropertiesDialog;
