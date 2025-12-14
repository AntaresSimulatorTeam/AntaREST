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

import FormDialog, { type FormDialogProps } from "@/components/dialogs/FormDialog";
import ListFE from "@/components/fieldEditors/ListFE";
import SelectFE from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import Fieldset from "@/components/Fieldset";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import { TABLE_MODE_TYPES } from "@/services/api/studies/tableMode/constants";
import storage, { StorageKey } from "@/services/utils/localStorage";
import { validateArray } from "@/utils/validation/array";
import { validateString } from "@/utils/validation/string";
import { useNavigate } from "@tanstack/react-router";
import startCase from "lodash/startCase";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { getTableColumnsForType, type TableTemplate } from "../../-utils";
import useStudy from "../../../../-hooks/useStudy";

export interface TableTemplateFormDialogProps
  extends Pick<FormDialogProps<TableTemplate>, "title" | "titleIcon" | "onCancel"> {
  defaultValues: TableTemplate;
  templates: TableTemplate[];
}

function TableTemplateFormDialog(props: TableTemplateFormDialogProps) {
  const { title, titleIcon, defaultValues, onCancel, templates } = props;
  const { t } = useTranslation();
  const navigate = useNavigate();
  const study = useStudy();
  const isUpdateDialog = !!defaultValues.name;

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
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<TableTemplate>) => {
    storage.setItem(StorageKey.StudiesModelTableModeTemplates, (prev) => {
      const currentTemplates = prev || [];

      return isUpdateDialog
        ? currentTemplates.map((template) =>
            template.name === defaultValues.name ? values : template,
          )
        : [...currentTemplates, values];
    });
  };

  const handleSubmitSuccessful = ({ values }: SubmitHandlerPlus<TableTemplate>) => {
    navigate({
      to: "/studies/$studyId/explore/tablemode/$tableModeId",
      params: { studyId: study.id, tableModeId: values.name },
      replace: isUpdateDialog ? true : false,
    });

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
      onSubmit={handleSubmit}
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
                existingValues: existingTables,
                editedValue: defaultValues?.name,
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
