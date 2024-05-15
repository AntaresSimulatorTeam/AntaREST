import { useTranslation } from "react-i18next";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { createTableTemplate, type TableTemplate } from "../utils";
import TableTemplateFormDialog, {
  TableTemplateFormDialogProps,
} from "./TableTemplateFormDialog";
import { SubmitHandlerPlus } from "../../../../../common/Form/types";

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
