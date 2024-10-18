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

import { useTranslation } from "react-i18next";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import Fieldset from "../Fieldset";
import FormDialog from "../dialogs/FormDialog";
import { SubmitHandlerPlus } from "../Form/types";
import StringFE from "../fieldEditors/StringFE";
import { validateString } from "@/utils/validation/string";

interface Props {
  open: boolean;
  onClose: VoidFunction;
  onSubmit: (name: string) => Promise<void>;
  existingNames: string[];
  defaultName: string;
}

function DuplicateDialog(props: Props) {
  const { open, onClose, onSubmit, existingNames, defaultName } = props;
  const { t } = useTranslation();
  const defaultValues = { name: defaultName };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({
    values: { name },
  }: SubmitHandlerPlus<typeof defaultValues>) => {
    await onSubmit(name);
    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open={open}
      title={t("global.duplicate")}
      titleIcon={ContentCopyIcon}
      onCancel={onClose}
      onSubmit={handleSubmit}
      config={{ defaultValues }}
      isCreationForm
    >
      {({ control }) => (
        <Fieldset fullFieldWidth>
          <StringFE
            label={t("global.name")}
            name="name"
            control={control}
            fullWidth
            rules={{
              validate: (v) =>
                validateString(v, { existingValues: existingNames }),
            }}
            sx={{ m: 0 }}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default DuplicateDialog;
