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

import FormDialog, { type FormDialogProps } from "@/components/dialogs/FormDialog";
import ListFE from "@/components/fieldEditors/ListFE";
import SelectFE from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import Fieldset from "@/components/Fieldset";
import { tableModeQueries } from "@/queries/tableMode/queries";
import type { TableMode } from "@/services/api/tablemode/types";
import { getNames } from "@/services/utils";
import { validateArray } from "@/utils/validation/array";
import { validateString } from "@/utils/validation/string";
import { useSuspenseQuery } from "@tanstack/react-query";
import startCase from "lodash/startCase";
import { useTranslation } from "react-i18next";
import { getTableColumnsForType, tableModeTypeOptions } from "./utils";

export interface TableModeFormDialogProps
  extends Pick<
    FormDialogProps<TableMode>,
    "title" | "titleIcon" | "onCancel" | "onSubmit" | "onSubmitSuccessful"
  > {
  defaultValues: TableMode;
}

function TableModeFormDialog(props: TableModeFormDialogProps) {
  const { title, titleIcon, defaultValues, onSubmit, onSubmitSuccessful, onCancel } = props;
  const { t } = useTranslation();

  const { data: existingNames } = useSuspenseQuery({
    ...tableModeQueries.list(),
    select: getNames,
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmitSuccessful: TableModeFormDialogProps["onSubmitSuccessful"] = (...args) => {
    onSubmitSuccessful?.(...args);
    onCancel();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open
      title={title}
      titleIcon={titleIcon}
      config={{ defaultValues }}
      onSubmit={onSubmit}
      onSubmitSuccessful={handleSubmitSuccessful}
      onCancel={onCancel}
    >
      {({ control, setValue, watch }) => (
        <Fieldset fullFieldWidth>
          <StringFE
            label={t("global.name")}
            name="name"
            autoFocus
            control={control}
            rules={{
              validate: validateString({
                existingValues: existingNames,
                editedValue: defaultValues.name,
              }),
            }}
          />
          <SelectFE
            label={t("study.type")}
            name="type"
            options={tableModeTypeOptions}
            variant="outlined"
            onChange={() => setValue("columns", [])}
            control={control}
          />
          <ListFE
            label={t("study.columns")}
            name="columns"
            options={[...getTableColumnsForType(watch("type"))]}
            getOptionLabel={startCase}
            getValueLabel={startCase}
            control={control}
            rules={{ validate: (v) => validateArray(v) }}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default TableModeFormDialog;
