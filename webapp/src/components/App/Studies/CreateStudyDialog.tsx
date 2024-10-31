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

import { AxiosError } from "axios";
import debug from "debug";
import { useSnackbar } from "notistack";
import * as R from "ramda";
import { useTranslation } from "react-i18next";
import { usePromise } from "react-use";

import { StudyPublicMode } from "@/common/types";
import FormDialog from "@/components/common/dialogs/FormDialog";
import CheckboxesTagsFE from "@/components/common/fieldEditors/CheckboxesTagsFE";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import StringFE from "@/components/common/fieldEditors/StringFE";
import Fieldset from "@/components/common/Fieldset";
import { SubmitHandlerPlus } from "@/components/common/Form/types";
import { PUBLIC_MODE_LIST } from "@/components/common/utils/constants";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { createStudy } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getGroups, getStudyVersionsFormatted } from "@/redux/selectors";

const logErr = debug("antares:createstudyform:error");

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

function CreateStudyDialog(props: Props) {
  const [t] = useTranslation();
  const { open, onClose } = props;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const versionList = useAppSelector(getStudyVersionsFormatted);
  const groupList = useAppSelector(getGroups);
  const mounted = usePromise();
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus<FieldValues>) => {
    const { name, ...rest } = data.values;

    if (name && name.replace(/\s+/g, "") !== "") {
      try {
        await mounted(
          dispatch(
            createStudy({
              name,
              ...rest,
            }),
          ).unwrap(),
        );

        enqueueSnackbar(t("studies.success.createStudy", { studyname: name }), {
          variant: "success",
        });
      } catch (e) {
        logErr("Failed to create new study", name, e);
        enqueueErrorSnackbar(
          t("studies.error.createStudy", { studyname: name }),
          e as AxiosError,
        );
      }
      onClose();
    } else {
      enqueueSnackbar(t("global.error.emptyName"), { variant: "error" });
    }
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
          <StringFE
            label={t("studies.studyName")}
            name="name"
            control={control}
            rules={{ required: true }}
            sx={{ mx: 0 }}
            fullWidth
          />

          <SelectFE
            label={t("global.version")}
            options={versionList.map((ver) => ({
              label: ver.name,
              value: ver.id,
            }))}
            name="version"
            control={control}
            sx={{ mt: 1, mb: 5 }}
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
              options={groupList.map((group) => group.name)}
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

export default CreateStudyDialog;
