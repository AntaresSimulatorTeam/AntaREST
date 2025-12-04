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

import ConfirmationDialog from "@/components/dialogs/ConfirmationDialog";
import EmptyView from "@/components/page/EmptyView";
import ViewWrapper from "@/components/page/ViewWrapper";
import PropertiesView from "@/components/PropertiesView";
import SplitView from "@/components/SplitView";
import TableMode from "@/components/TableMode";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import { Button } from "@mui/material";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import { useUpdateEffect } from "react-use";
import { v4 as uuidv4 } from "uuid";
import storage, { StorageKey } from "../../../../../services/utils/localStorage";
import type { StudyMetadata } from "../../../../../types/types";
import ListElement from "../common/ListElement";
import CreateTemplateTableDialog from "./dialogs/CreateTemplateTableDialog";
import UpdateTemplateTableDialog from "./dialogs/UpdateTemplateTableDialog";
import type { TableTemplate } from "./utils";

function TableModeList() {
  const { t } = useTranslation();

  const [templates, setTemplates] = useState<TableTemplate[]>(() => {
    const list = storage.getItem(StorageKey.StudiesModelTableModeTemplates) || [];
    return list.map((tp) => ({ ...tp, id: uuidv4() }));
  });

  const [selectedTemplateId, setSelectedTemplateId] = useState<TableTemplate["id"] | undefined>(
    templates[0]?.id,
  );

  const [dialog, setDialog] = useState<{
    type: "add" | "edit" | "delete";
    templateId: TableTemplate["id"];
  } | null>(null);

  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const selectedTemplate = templates.find((tp) => tp.id === selectedTemplateId);
  const dialogTemplate = dialog && templates.find((tp) => tp.id === dialog.templateId);

  // Handle automatic selection of the first element
  useEffect(() => {
    if (templates.length > 0 && !selectedTemplate) {
      setSelectedTemplateId(templates[0].id);
    }
  }, [templates, selectedTemplate]);

  // Update local storage
  useUpdateEffect(() => {
    storage.setItem(
      StorageKey.StudiesModelTableModeTemplates,
      templates
        // It is useless to keep template ids in local storage
        .map(({ id, ...rest }) => rest),
    );
  }, [templates]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const closeDialog = () => setDialog(null);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleEditClick = () => {
    if (selectedTemplate) {
      setDialog({
        type: "edit",
        templateId: selectedTemplate.id,
      });
    }
  };

  const handleDeleteClick = () => {
    if (selectedTemplate) {
      setDialog({
        type: "delete",
        templateId: selectedTemplate.id,
      });
    }
  };

  const handleDelete = () => {
    setTemplates((templates) => templates.filter((tp) => tp.id !== dialog?.templateId));
    closeDialog();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <SplitView splitId="tablemode">
        {/* Left */}
        <PropertiesView
          mainContent={
            <ListElement
              list={templates}
              currentElement={selectedTemplate?.id}
              currentElementKeyToTest="id"
              setSelectedItem={({ id }) => setSelectedTemplateId(id)}
            />
          }
          onAdd={() => setDialog({ type: "add", templateId: "" })}
        />
        {/* Right */}
        <ViewWrapper>
          {!templates.length && <EmptyView title={t("study.tableMode.empty")} />}
          {selectedTemplate && (
            <TableMode
              studyId={study.id}
              type={selectedTemplate.type}
              columns={selectedTemplate.columns}
              extraActions={
                <>
                  <Button variant="outlined" startIcon={<EditIcon />} onClick={handleEditClick}>
                    {t("global.edit")}
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={handleDeleteClick}
                  >
                    {t("global.delete")}
                  </Button>
                </>
              }
            />
          )}
        </ViewWrapper>
      </SplitView>
      {dialog?.type === "add" && (
        <CreateTemplateTableDialog
          templates={templates}
          setTemplates={setTemplates}
          onCancel={closeDialog}
          open
        />
      )}
      {dialog?.type === "edit" && dialogTemplate && (
        <UpdateTemplateTableDialog
          defaultValues={dialogTemplate}
          templates={templates}
          setTemplates={setTemplates}
          onCancel={closeDialog}
          open
        />
      )}
      {dialog?.type === "delete" && dialogTemplate && (
        <ConfirmationDialog
          titleIcon={DeleteIcon}
          alert="warning"
          onConfirm={handleDelete}
          onCancel={closeDialog}
          open
        >
          {t("study.tableMode.dialog.delete.text", {
            name: dialogTemplate.name,
          })}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default TableModeList;
