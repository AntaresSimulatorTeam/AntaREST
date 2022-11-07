import { useState } from "react";
import { MenuItem } from "@mui/material";
import { useOutletContext } from "react-router";
import { useUpdateEffect } from "react-use";
import { useTranslation } from "react-i18next";
import DeleteIcon from "@mui/icons-material/Delete";
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
  DEFAULT_TABLE_TEMPLATE_NAMES,
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
  const [templates, setTemplates] = useState(() => [
    ...DEFAULT_TABLE_TEMPLATES,
    ...(storage.getItem(StorageKey.StudiesModelTableModeTemplates) || []),
  ]);
  const [selectedTemplateName, setSelectedTemplateName] = useState(
    templates[0].name
  );
  const selectedTemplate =
    templates.find((t) => t.name === selectedTemplateName) || templates[0];
  const [dialog, setDialog] = useState<{
    type: "add" | "edit" | "delete";
    templateName: string;
  } | null>(null);
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { t } = useTranslation();

  const res = usePromise(async () => {
    const { type, columns } = selectedTemplate;
    return api.getTableData(study.id, type, columns);
  }, [selectedTemplate]);

  // Update local storage
  useUpdateEffect(() => {
    storage.setItem(
      StorageKey.StudiesModelTableModeTemplates,
      templates.filter((t) => !DEFAULT_TABLE_TEMPLATE_NAMES.includes(t.name))
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
      templates.filter((t) => t.name !== dialog?.templateName)
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
                currentElement={selectedTemplate.name}
                setSelectedItem={({ name }) => setSelectedTemplateName(name)}
                contextMenuContent={({ element, close }) => {
                  const isNotAllowed = DEFAULT_TABLE_TEMPLATE_NAMES.includes(
                    element.name
                  );
                  return (
                    <>
                      <MenuItem
                        onClick={(event) => {
                          event.stopPropagation();
                          setDialog({
                            type: "edit",
                            templateName: element.name,
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
                            templateName: element.name,
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
            onAdd={() => setDialog({ type: "add", templateName: "" })}
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
            templates.find(
              (t) => t.name === dialog.templateName
            ) as TableTemplate
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
            dialog.templateName,
          ])}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default TableMode;
