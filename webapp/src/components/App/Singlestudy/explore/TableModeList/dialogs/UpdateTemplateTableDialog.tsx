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

import EditIcon from "@mui/icons-material/Edit";

import { SubmitHandlerPlus } from "@/components/common/Form/types";

import { TableTemplate } from "../utils";

import TableTemplateFormDialog, {
  TableTemplateFormDialogProps,
} from "./TableTemplateFormDialog";

interface Props
  extends Pick<TableTemplateFormDialogProps, "open" | "onCancel"> {
  defaultValues: TableTemplate;
  setTemplates: React.Dispatch<React.SetStateAction<TableTemplate[]>>;
  templates: TableTemplate[];
}

function UpdateTemplateTableDialog(props: Props) {
  const { open, onCancel, defaultValues, setTemplates, templates } = props;
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    setTemplates((templates) =>
      templates.map((t) => (t.id === data.values.id ? data.values : t)),
    );

    onCancel();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TableTemplateFormDialog
      open={open}
      title={t("study.tableMode.dialog.edit.title")}
      titleIcon={EditIcon}
      config={{ defaultValues }}
      onSubmit={handleSubmit}
      onCancel={onCancel}
      templates={templates}
    />
  );
}

export default UpdateTemplateTableDialog;
