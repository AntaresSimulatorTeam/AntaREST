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

import { useTranslation } from "react-i18next";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useOutletContext } from "react-router";
import { useMemo } from "react";
import FormDialog from "../../../../../../../common/dialogs/FormDialog";
import StringFE from "../../../../../../../common/fieldEditors/StringFE";
import type { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import type { StudyMetadata } from "../../../../../../../../types/types";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../../../common/Fieldset";
import useAppDispatch from "../../../../../../../../redux/hooks/useAppDispatch";
import { createStudyMapDistrict } from "../../../../../../../../redux/ducks/studyMaps";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getStudyMapDistrictsById } from "../../../../../../../../redux/selectors";
import { validateString } from "@/utils/validation/string";

interface Props {
  open: boolean;
  onClose: () => void;
}

const defaultValues = {
  name: "",
  output: true,
  comments: "",
};

function CreateDistrictDialog(props: Props) {
  const { open, onClose } = props;
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const districtsById = useAppSelector(getStudyMapDistrictsById);

  const existingDistricts = useMemo(
    () => Object.values(districtsById).map(({ name }) => name),
    [districtsById],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    const { name, output, comments } = data.values;

    return dispatch(
      createStudyMapDistrict({
        studyId: study.id,
        name,
        output,
        comments,
      }),
    )
      .unwrap()
      .then(onClose);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("study.modelization.map.districts.add")}
      titleIcon={AddCircleIcon}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      config={{
        defaultValues,
      }}
    >
      {({ control }) => (
        <Fieldset fullFieldWidth>
          <StringFE
            label={t("global.name")}
            name="name"
            control={control}
            fullWidth
            rules={{
              validate: (v) => validateString(v, { existingValues: existingDistricts }),
            }}
            sx={{ m: 0 }}
          />
          <SwitchFE
            name="output"
            label={t("study.modelization.map.districts.field.outputs")}
            control={control}
            sx={{ ".MuiFormControlLabel-root": { m: 0 } }}
          />
          <StringFE
            name="comments"
            label={t("study.modelization.map.districts.field.comments")}
            control={control}
            fullWidth
            sx={{ m: 0 }}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CreateDistrictDialog;
