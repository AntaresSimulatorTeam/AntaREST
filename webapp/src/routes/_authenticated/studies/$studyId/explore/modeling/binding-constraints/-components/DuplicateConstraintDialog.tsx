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
import { bindingConstraintQueries } from "@/queries/bindingConstraints";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import type { BindingConstraint } from "@/services/api/studies/bindingConstraints/type";
import { getNames } from "@/services/utils";
import { validateString } from "@/utils/validation/string";
import ContentCopy from "@mui/icons-material/ContentCopy";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import useDuplicateBindingConstraint from "../-hooks/useDuplicateBindingConstraint";

interface Props {
  constraintToDuplicate: BindingConstraint;
  onCancel: VoidFunction;
}

function DuplicateConstraintDialog({ constraintToDuplicate, onCancel }: Props) {
  const study = useStudy();
  const { t } = useTranslation();
  const duplicateConstraint = useDuplicateBindingConstraint();

  const { data: existingNames } = useSuspenseQuery({
    ...bindingConstraintQueries.list(study.id),
    select: getNames,
  });

  const defaultValues = {
    name: `${constraintToDuplicate.name} (copy)`,
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<typeof defaultValues>) => {
    duplicateConstraint.mutate({
      studyId: study.id,
      constraintId: constraintToDuplicate.id,
      newConstraintName: values.name,
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open
      title={t("study.modeling.bindingConst.duplicate")}
      titleIcon={ContentCopy}
      maxWidth="sm"
      onCancel={onCancel}
      onSubmit={handleSubmit}
      onSubmitSuccessful={onCancel}
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
              existingValues: existingNames,
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
