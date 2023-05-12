import { DialogProps } from "@mui/material";
import TextField from "@mui/material/TextField";
import { useSnackbar } from "notistack";
import * as R from "ramda";
import { useTranslation } from "react-i18next";
import { usePromise } from "react-use";
import { StudyMetadata } from "../../../common/types";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import { moveStudy } from "../../../services/api/study";
import { isStringEmpty } from "../../../services/utils";
import FormDialog from "../../common/dialogs/FormDialog";
import { SubmitHandlerPlus } from "../../common/Form/types";

interface Props extends DialogProps {
  study: StudyMetadata;
  onClose: () => void;
}

function MoveStudyDialog(props: Props) {
  const { study, open, onClose } = props;
  const [t] = useTranslation();
  const mounted = usePromise();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const defaultValues = {
    folder: R.join("/", R.dropLast(1, R.split("/", study.folder || ""))),
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (
    data: SubmitHandlerPlus<typeof defaultValues>
  ) => {
    const { folder } = data.values;
    try {
      await mounted(moveStudy(study.id, folder));
      enqueueSnackbar(
        t("studies.success.moveStudy", { study: study.name, folder }),
        {
          variant: "success",
        }
      );
      onClose();
    } catch (e) {
      enqueueErrorSnackbar(
        t("studies.error.moveStudy", { study: study.name }),
        e as Error
      );
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open={open}
      config={{ defaultValues }}
      onSubmit={handleSubmit}
      onCancel={onClose}
    >
      {(formObj) => (
        <TextField
          sx={{ mx: 0 }}
          autoFocus
          label={t("studies.folder")}
          error={!!formObj.formState.errors.folder}
          helperText={formObj.formState.errors.folder?.message}
          placeholder={t("studies.movefolderplaceholder") as string}
          InputLabelProps={
            // Allow to show placeholder when field is empty
            formObj.formState.defaultValues?.folder ? { shrink: true } : {}
          }
          fullWidth
          {...formObj.register("folder", {
            required: t("form.field.required") as string,
            validate: (value) => {
              return !isStringEmpty(value);
            },
          })}
        />
      )}
    </FormDialog>
  );
}

export default MoveStudyDialog;
