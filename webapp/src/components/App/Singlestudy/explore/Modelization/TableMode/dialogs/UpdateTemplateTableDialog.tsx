import { useTranslation } from "react-i18next";
import EditIcon from "@mui/icons-material/Edit";
import TableTemplateFormDialog, {
  TableTemplateFormDialogProps,
} from "./TableTemplateFormDialog";
import { TableTemplate } from "../utils";
import { SubmitHandlerPlus } from "../../../../../../common/Form/types";

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
      templates.map((t) => (t.id === data.values.id ? data.values : t))
    );

    onCancel();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TableTemplateFormDialog
      open={open}
      title={t("study.modelization.tableMode.dialog.edit.title")}
      titleIcon={EditIcon}
      config={{ defaultValues }}
      onSubmit={handleSubmit}
      onCancel={onCancel}
      templates={templates}
    />
  );
}

export default UpdateTemplateTableDialog;
