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
import SelectFE from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import Fieldset from "@/components/Fieldset";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import { reserveTypeSchema } from "@/services/api/studies/areas/reserves/schemas";
import type { ReserveType } from "@/services/api/studies/areas/reserves/types";
import { validateString } from "@/utils/validation/string";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useTranslation } from "react-i18next";

export interface CreateReserveValues {
  name: string;
  type: ReserveType;
}

interface Props {
  open: boolean;
  onClose: VoidFunction;
  onSubmit: (values: CreateReserveValues) => Promise<void>;
  existingNames: string[];
}

const RESERVE_TYPES = reserveTypeSchema.options;

function CreateReserveDialog({ open, onClose, onSubmit, existingNames }: Props) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values: { name, type } }: SubmitHandlerPlus<CreateReserveValues>) => {
    return onSubmit({ name: name.trim(), type });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("button.add")}
      titleIcon={AddCircleIcon}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
    >
      {({ control }) => (
        <Fieldset fullFieldWidth>
          <StringFE
            label={t("global.name")}
            name="name"
            control={control}
            fullWidth
            rules={{
              validate: (v) => validateString(v, { existingValues: existingNames }),
            }}
            sx={{ m: 0 }}
          />
          <SelectFE
            label={t("global.type")}
            name="type"
            control={control}
            options={RESERVE_TYPES}
            rules={{ required: t("form.field.required") }}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CreateReserveDialog;
