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

import type { AxiosError } from "axios";
import debug from "debug";
import { useSnackbar } from "notistack";
import * as R from "ramda";
import { useTranslation } from "react-i18next";
import { usePromise } from "react-use";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import { openExternalStudy } from "../../../redux/ducks/studies";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { getStudyVersionsFormatted } from "../../../redux/selectors";
import type { StudyPublicMode } from "../../../types/types";
import FormDialog from "../../common/dialogs/FormDialog";
import StringFE from "../../common/fieldEditors/StringFE";
import Fieldset from "../../common/Fieldset";
import type { SubmitHandlerPlus } from "../../common/Form/types";

const logErr = debug("antares:createstudyform:error");

interface FieldValues {
  path: string;
}

interface Props {
  open: boolean;
  onClose: VoidFunction;
}

function OpenExternalDialog(props: Props) {
  const [t] = useTranslation();
  const { open, onClose } = props;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const versionList = useAppSelector(getStudyVersionsFormatted);
  const mounted = usePromise();
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus<FieldValues>) => {
    const { path } = data.values;

    if (path && path.replace(/\s+/g, "") !== "") {
      try {
        await mounted(
          dispatch(
            openExternalStudy({
              path,
            }),
          ).unwrap(),
        );

        enqueueSnackbar(t("studies.success.createStudy", { studyname: name }), {
          variant: "success",
        });
      } catch (e) {
        logErr("Failed to create new study", name, e);
        enqueueErrorSnackbar(t("studies.error.createStudy", { studyname: name }), e as AxiosError);
      }
      //   onClose();
    } else {
      enqueueSnackbar(t("global.error.emptyName"), { variant: "error" });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("studies.openExternal")}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      config={{
        defaultValues: {
          path: "",
        },
      }}
    >
      {({ control }) => (
        <>
          <Fieldset fullFieldWidth>
            <StringFE
              label={"full path of study"}
              name="path"
              control={control}
              rules={{ required: true }}
            />
          </Fieldset>
        </>
      )}
    </FormDialog>
  );
}

export default OpenExternalDialog;
