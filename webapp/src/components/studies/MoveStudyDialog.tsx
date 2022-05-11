import { DialogProps } from "@mui/material";
import TextField from "@mui/material/TextField";
import { useSnackbar } from "notistack";
import { dropLast, join, split } from "ramda";
import { useTranslation } from "react-i18next";
import { usePromise } from "react-use";
import { StudyMetadata } from "../../common/types";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar";
import { moveStudy } from "../../services/api/study";
import { isStringEmpty } from "../../services/utils";
import FormDialog, { SubmitHandlerData } from "../common/dialogs/FormDialog";

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

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerData) => {
    const { folder } = data.values;
    try {
      await mounted(moveStudy(study.id, folder));
      enqueueSnackbar(
        t("studymanager:moveStudySuccess", { study: study.name, folder }),
        {
          variant: "success",
        }
      );
      onClose();
    } catch (e) {
      enqueueErrorSnackbar(
        t("studymanager:moveStudyFailure", { study: study.name }),
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
      formOptions={{
        defaultValues: {
          folder: join("/", dropLast(1, split("/", study.folder || ""))),
        },
      }}
      onSubmit={handleSubmit}
      onCancel={onClose}
    >
      {(formObj) => (
        <TextField
          sx={{ mx: 0 }}
          autoFocus
          label={t("studymanager:folder")}
          error={!!formObj.formState.errors.folder}
          helperText={formObj.formState.errors.folder?.message}
          placeholder={t("studymanager:movefolderplaceholder") as string}
          InputLabelProps={
            // Allow to show placeholder when field is empty
            formObj.defaultValues?.folder ? { shrink: true } : {}
          }
          fullWidth
          {...formObj.register("folder", {
            required: t("main:form.field.required") as string,
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
