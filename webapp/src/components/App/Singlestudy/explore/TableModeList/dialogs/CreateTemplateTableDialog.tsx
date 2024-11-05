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

import AddCircleIcon from "@mui/icons-material/AddCircle";

import { SubmitHandlerPlus } from "@/components/common/Form/types";

import { createTableTemplate, TableTemplate } from "../utils";

import TableTemplateFormDialog, {
  TableTemplateFormDialogProps,
} from "./TableTemplateFormDialog";

interface Props
  extends Pick<TableTemplateFormDialogProps, "open" | "onCancel"> {
  setTemplates: React.Dispatch<React.SetStateAction<TableTemplate[]>>;
  templates: TableTemplate[];
}

function CreateTemplateTableDialog(props: Props) {
  const { open, onCancel, setTemplates, templates } = props;
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<TableTemplate>) => {
    const { name, type, columns } = data.values;

    setTemplates((templates) => [
      ...templates,
      createTableTemplate(name, type, columns),
    ]);

    onCancel();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TableTemplateFormDialog
      open={open}
      title={t("study.tableMode.dialog.add.title")}
      titleIcon={AddCircleIcon}
      config={{
        defaultValues: {
          name: "",
          type: "areas",
          columns: [],
        },
      }}
      onSubmit={handleSubmit}
      onCancel={onCancel}
      templates={templates}
    />
  );
}

export default CreateTemplateTableDialog;
