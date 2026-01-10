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
import StringFE from "@/components/fieldEditors/StringFE";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import { validateString } from "@/utils/validation/string";
import ContentCopy from "@mui/icons-material/ContentCopy";
import { useTranslation } from "react-i18next";
import type { BindingConstraint } from "../-utils";

interface Props {
  open: boolean;
  onClose: VoidFunction;
  constraintName: string;
  existingConstraints: Array<BindingConstraint["id"]>;
  onDuplicate: (newName: string) => Promise<void>;
}

function DuplicateConstraintDialog({
  open,
  onClose,
  constraintName,
  existingConstraints,
  onDuplicate,
}: Props) {
  const [t] = useTranslation();

  const defaultValues = {
    name: `${constraintName} (copy)`,
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<typeof defaultValues>) => {
    return onDuplicate(values.name);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("study.modeling.bindingConst.duplicate")}
      titleIcon={ContentCopy}
      maxWidth="sm"
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      onSubmitSuccessful={onClose}
      config={{ defaultValues }}
      allowSubmitOnPristine
    >
      {({ control }) => (
        <StringFE
          label={t("global.name")}
          name="name"
          control={control}
          fullWidth
          rules={{
            validate: validateString({
              existingValues: existingConstraints,
              specialChars: "@&_-()",
            }),
          }}
          margin="dense"
        />
      )}
    </FormDialog>
  );
}

export default DuplicateConstraintDialog;
