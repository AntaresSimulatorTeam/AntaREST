import { useTranslation } from "react-i18next";
import EditIcon from "@mui/icons-material/Edit";
import TableTemplateFormDialog, {
  TableTemplateFormDialogProps,
} from "./TableTemplateFormDialog";
import { TableTemplate } from "../utils";
import { SubmitHandlerPlus } from "../../../../../../common/Form";

interface Props
  extends Pick<TableTemplateFormDialogProps, "open" | "onCancel"> {
  defaultValues: TableTemplate;
  setTemplates: React.Dispatch<React.SetStateAction<TableTemplate[]>>;
}

function UpdateTemplateTableDialog(props: Props) {
  const { open, onCancel, defaultValues, setTemplates } = props;
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    setTemplates((templates) =>
      templates.map((t) => (t.name === data.values.name ? data.values : t))
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
      disableName
    />
  );
}

export default UpdateTemplateTableDialog;
