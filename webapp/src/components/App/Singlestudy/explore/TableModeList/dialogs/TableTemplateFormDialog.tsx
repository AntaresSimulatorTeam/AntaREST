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

import SelectFE from "@/components/common/fieldEditors/SelectFE";
import Fieldset from "@/components/common/Fieldset";
import { validateArray } from "@/utils/validation/array";
import { validateString } from "@/utils/validation/string";
import startCase from "lodash/startCase";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { TABLE_MODE_TYPES } from "../../../../../../services/api/studies/tableMode/constants";
import FormDialog, { type FormDialogProps } from "../../../../../common/dialogs/FormDialog";
import ListFE from "../../../../../common/fieldEditors/ListFE";
import StringFE from "../../../../../common/fieldEditors/StringFE";
import { getTableColumnsForType, type TableTemplate } from "../utils";

export interface TableTemplateFormDialogProps
  extends Pick<
    FormDialogProps<TableTemplate>,
    "open" | "title" | "titleIcon" | "onSubmit" | "onCancel" | "config"
  > {
  templates: TableTemplate[];
}

function TableTemplateFormDialog(props: TableTemplateFormDialogProps) {
  const { open, title, titleIcon, config, onSubmit, onCancel, templates } = props;
  const { t } = useTranslation();

  const existingTables = useMemo(() => templates.map(({ name }) => name), [templates]);

  const typeOptions = useMemo(
    () =>
      TABLE_MODE_TYPES.map((type) => ({
        value: type,
        label: t(`tableMode.type.${type}`),
      })),
    [t],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open={open}
      title={title}
      titleIcon={titleIcon}
      config={config}
      onSubmit={onSubmit}
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
                existingValues: existingTables,
                editedValue: config?.defaultValues?.name,
              }),
            }}
          />
          <SelectFE
            label={t("study.type")}
            options={typeOptions}
            variant="outlined"
            onChange={() => setValue("columns", [])}
            name="type"
            control={control}
          />
          <ListFE
            label={t("study.columns")}
            options={[...getTableColumnsForType(watch("type"))]}
            getOptionLabel={startCase}
            name="columns"
            control={control}
            rules={{ validate: validateArray() }}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default TableTemplateFormDialog;
