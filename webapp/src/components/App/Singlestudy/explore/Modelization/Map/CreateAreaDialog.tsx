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
import FormDialog from "../../../../../common/dialogs/FormDialog";
import StringFE from "../../../../../common/fieldEditors/StringFE";
import type { SubmitHandlerPlus } from "../../../../../common/Form/types";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getAreas } from "../../../../../../redux/selectors";
import Fieldset from "../../../../../common/Fieldset";
import { validateString } from "@/utils/validation/string";

interface Props {
  studyId: string;
  open: boolean;
  onClose: () => void;
  createArea: (name: string) => void;
}

function CreateAreaDialog(props: Props) {
  const { studyId, open, onClose, createArea } = props;
  const [t] = useTranslation();
  const existingAreas = useAppSelector((state) =>
    getAreas(state, studyId).map((area) => area.name),
  );

  const defaultValues = {
    name: "",
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    return createArea(data.values.name.trim());
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("study.modelization.map.newArea")}
      titleIcon={AddCircleIcon}
      maxWidth="sm"
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
              validate: (v) => validateString(v, { existingValues: existingAreas }),
            }}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CreateAreaDialog;
