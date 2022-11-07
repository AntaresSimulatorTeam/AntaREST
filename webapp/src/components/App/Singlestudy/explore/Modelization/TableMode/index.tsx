import { useState } from "react";
import { MenuItem } from "@mui/material";
import { useOutletContext } from "react-router";
import { useUpdateEffect } from "react-use";
import { useTranslation } from "react-i18next";
import DeleteIcon from "@mui/icons-material/Delete";
import { v4 as uuidv4 } from "uuid";
import PropertiesView from "../../../../../common/PropertiesView";
import SplitLayoutView from "../../../../../common/SplitLayoutView";
import ListElement from "../../common/ListElement";
import usePromise from "../../../../../../hooks/usePromise";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import { SubmitHandlerPlus } from "../../../../../common/Form";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import FormTable from "../../../../../common/FormTable";
import {
  DEFAULT_TABLE_TEMPLATES,
  DEFAULT_TABLE_TEMPLATE_IDS,
  TableData,
  TableTemplate,
} from "./utils";
import storage, {
  StorageKey,
} from "../../../../../../services/utils/localStorage";
import { StudyMetadata } from "../../../../../../common/types";
import CreateTemplateTableDialog from "./dialogs/CreateTemplateTableDialog";
import UpdateTemplateTableDialog from "./dialogs/UpdateTemplateTableDialog";
import ConfirmationDialog from "../../../../../common/dialogs/ConfirmationDialog";
import * as api from "../../../../../../services/api/forms/tableMode";

function TableMode() {
  const { t } = useTranslation();
  const [templates, setTemplates] = useState(() => [
    ...DEFAULT_TABLE_TEMPLATES.map((tp) => ({
      ...tp,
      name: t(`study.modelization.tableMode.template.${tp.name}`),
    })),
    ...(storage.getItem(StorageKey.StudiesModelTableModeTemplates) || []).map(
      (tp) => ({ ...tp, id: uuidv4() })
    ),
  ]);
  const [selectedTemplateId, setSelectedTemplateId] = useState(templates[0].id);
  const selectedTemplate =
    templates.find((tp) => tp.id === selectedTemplateId) || templates[0];
  const [dialog, setDialog] = useState<{
    type: "add" | "edit" | "delete";
    templateId: TableTemplate["id"];
  } | null>(null);
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  const res = usePromise(async () => {
    const { type, columns } = selectedTemplate;
    return api.getTableData(study.id, type, columns);
  }, [selectedTemplate]);

  // Update local storage
  useUpdateEffect(() => {
    storage.setItem(
      StorageKey.StudiesModelTableModeTemplates,
      templates
        .filter((tp) => !DEFAULT_TABLE_TEMPLATE_IDS.includes(tp.id))
        // It is useless to keep template ids in local storage
        .map(({ id, ...rest }) => rest)
    );
  }, [templates]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const closeDialog = () => setDialog(null);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<TableData>) => {
    return api.setTableData(study.id, selectedTemplate.type, data.dirtyValues);
  };

  const handleDeleteTemplate = () => {
    setTemplates((templates) =>
      templates.filter((tp) => tp.id !== dialog?.templateId)
    );
    closeDialog();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <SplitLayoutView
        left={
          <PropertiesView
            mainContent={
              <ListElement
                list={templates}
                currentElement={selectedTemplate.id}
                currentElementKeyToTest="id"
                setSelectedItem={({ id }) => setSelectedTemplateId(id)}
                contextMenuContent={({ element, close }) => {
                  const isNotAllowed = DEFAULT_TABLE_TEMPLATE_IDS.includes(
                    element.id
                  );
                  return (
                    <>
                      <MenuItem
                        onClick={(event) => {
                          event.stopPropagation();
                          setDialog({
                            type: "edit",
                            templateId: element.id,
                          });
                          close();
                        }}
                        disabled={isNotAllowed}
                      >
                        Edit
                      </MenuItem>
                      <MenuItem
                        onClick={(event) => {
                          event.stopPropagation();
                          setDialog({
                            type: "delete",
                            templateId: element.id,
                          });
                          close();
                        }}
                        disabled={isNotAllowed}
                      >
                        Delete
                      </MenuItem>
                    </>
                  );
                }}
              />
            }
            onAdd={() => setDialog({ type: "add", templateId: "" })}
          />
        }
        right={
          <UsePromiseCond
            response={res}
            ifPending={() => <SimpleLoader />}
            ifResolved={(data) => (
              <FormTable
                defaultValues={data}
                onSubmit={handleSubmit}
                tableProps={{
                  columns: selectedTemplate.columns,
                  height: "100%",
                  width: "100%",
                }}
              />
            )}
          />
        }
      />
      {dialog?.type === "add" && (
        <CreateTemplateTableDialog
          templates={templates}
          setTemplates={setTemplates}
          onCancel={closeDialog}
          open
        />
      )}
      {dialog?.type === "edit" && (
        <UpdateTemplateTableDialog
          defaultValues={
            templates.find((tp) => tp.id === dialog.templateId) as TableTemplate
          }
          setTemplates={setTemplates}
          onCancel={closeDialog}
          open
        />
      )}
      {dialog?.type === "delete" && (
        <ConfirmationDialog
          titleIcon={DeleteIcon}
          alert="warning"
          onConfirm={handleDeleteTemplate}
          onCancel={closeDialog}
          open
        >
          {t("study.modelization.tableMode.dialog.delete.text", [
            templates.find((tp) => tp.id === dialog.templateId)?.name,
          ])}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default TableMode;
