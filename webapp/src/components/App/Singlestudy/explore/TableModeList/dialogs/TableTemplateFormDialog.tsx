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

import { Box } from "@mui/material";
import { startCase } from "lodash";
import { useTranslation } from "react-i18next";
import FormDialog, {
  FormDialogProps,
} from "../../../../../common/dialogs/FormDialog";
import ListFE from "../../../../../common/fieldEditors/ListFE";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../common/fieldEditors/StringFE";
import { getTableColumnsForType, type TableTemplate } from "../utils";
import { TABLE_MODE_TYPES } from "../../../../../../services/api/studies/tableMode/constants";
import { validateString } from "../../../../../../utils/validationUtils";
import { useMemo } from "react";

export interface TableTemplateFormDialogProps
  extends Pick<
    FormDialogProps<TableTemplate>,
    "open" | "title" | "titleIcon" | "onSubmit" | "onCancel" | "config"
  > {
  templates: TableTemplate[];
}

function TableTemplateFormDialog(props: TableTemplateFormDialogProps) {
  const { open, title, titleIcon, config, onSubmit, onCancel, templates } =
    props;
  const { t } = useTranslation();

  const existingTables = useMemo(
    () => templates.map(({ name }) => name),
    [templates],
  );

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
      {({ control, setValue, getValues }) => (
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 2,
          }}
        >
          <StringFE
            sx={{ m: 0 }}
            label={t("global.name")}
            name="name"
            autoFocus
            control={control}
            rules={{
              validate: (v) =>
                validateString(v, {
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
            options={[...getTableColumnsForType(getValues("type"))]}
            getOptionLabel={startCase}
            name="columns"
            control={control}
            rules={{ required: true }}
          />
        </Box>
      )}
    </FormDialog>
  );
}

export default TableTemplateFormDialog;
