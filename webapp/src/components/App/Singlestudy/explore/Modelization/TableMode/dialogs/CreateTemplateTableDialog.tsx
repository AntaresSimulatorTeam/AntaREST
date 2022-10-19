import { useTranslation } from "react-i18next";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import {
  createTableTemplate,
  TableTemplate,
  TableTemplateType,
} from "../utils";
import TableTemplateFormDialog, {
  TableTemplateFormDialogProps,
} from "./TableTemplateFormDialog";
import { SubmitHandlerPlus } from "../../../../../../common/Form";

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
      title={t("study.modelization.tableMode.dialog.add.title")}
      titleIcon={AddCircleIcon}
      config={{
        defaultValues: {
          name: "",
          type: TableTemplateType.Area,
          columns: [],
        },
      }}
      onSubmit={handleSubmit}
      onCancel={onCancel}
      rulesForName={{
        validate: (value) => {
          if (templates.find((t) => t.name === value)) {
            return t("form.field.notAllowedValue") as string;
          }
        },
      }}
    />
  );
}

export default CreateTemplateTableDialog;
