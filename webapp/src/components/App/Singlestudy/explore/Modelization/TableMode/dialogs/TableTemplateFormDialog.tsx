import { Box } from "@mui/material";
import { startCase } from "lodash";
import { useTranslation } from "react-i18next";
import FormDialog, {
  FormDialogProps,
} from "../../../../../../common/dialogs/FormDialog";
import ListFE from "../../../../../../common/fieldEditors/ListFE";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../../common/fieldEditors/StringFE";
import {
  getTableColumnsForType,
  TableTemplate,
  TABLE_TEMPLATE_TYPE_OPTIONS,
} from "../utils";

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

  return (
    <FormDialog
      open={open}
      title={title}
      titleIcon={titleIcon}
      config={config}
      onSubmit={onSubmit}
      onCancel={onCancel}
    >
      {({ control, resetField, getValues }) => (
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
              validate: (value) => {
                const id = getValues("id");
                const hasDuplicate = templates.find(
                  (tp) => tp.id !== id && tp.name.trim() === value.trim()
                );
                if (hasDuplicate) {
                  return t("form.field.notAllowedValue") as string;
                }
              },
              required: true,
            }}
          />
          <SelectFE
            label={t("study.type")}
            options={TABLE_TEMPLATE_TYPE_OPTIONS}
            variant="outlined"
            onChange={() => resetField("columns")}
            name="type"
            control={control}
          />
          <ListFE
            label={t("study.columns")}
            options={getTableColumnsForType(getValues("type"))}
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
