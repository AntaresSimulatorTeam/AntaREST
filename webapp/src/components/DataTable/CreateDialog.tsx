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

import { validateString } from "@/utils/validation/string";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useTranslation } from "react-i18next";
import FormDialog from "../dialogs/FormDialog";
import SelectFE from "../fieldEditors/SelectFE";
import StringFE from "../fieldEditors/StringFE";
import Fieldset from "../Fieldset";
import type { SubmitHandlerPlus } from "../Form/types";
import type { RowData } from "./types";

interface Props {
  open: boolean;
  onClose: VoidFunction;
  onSubmit: (values: RowData) => Promise<void>;
  groups?: string[];
  allowNewGroups?: boolean;
  existingNames: Array<RowData["name"]>;
}

function CreateDialog({ open, onClose, onSubmit, groups, allowNewGroups, existingNames }: Props) {
  const { t } = useTranslation();
  const hasGroups = groups !== undefined;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values: { name, group } }: SubmitHandlerPlus<RowData>) => {
    return onSubmit(hasGroups ? { name: name.trim(), group } : { name: name.trim() });
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
          {hasGroups &&
            (allowNewGroups ? (
              <StringFE
                label={t("global.group")}
                name="group"
                datalist={groups}
                control={control}
                rules={{ required: t("form.field.required") }}
              />
            ) : (
              <SelectFE
                label={t("global.group")}
                name="group"
                control={control}
                options={groups}
                rules={{ required: t("form.field.required") }}
              />
            ))}
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CreateDialog;
