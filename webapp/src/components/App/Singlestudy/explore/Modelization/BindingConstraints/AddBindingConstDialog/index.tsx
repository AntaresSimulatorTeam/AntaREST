/* eslint-disable camelcase */
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import FormDialog, {
  FormDialogProps,
} from "../../../../../../common/dialogs/FormDialog";
import AddBindingConstForm from "./AddBindingConstForm";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import { appendCommands } from "../../../../../../../services/api/variant";
import {
  BindingConstraintOperator,
  CommandEnum,
  CreateBindingConstraint,
  TimeStep,
} from "../../../../Commands/Edition/commandTypes";
import { SubmitHandlerPlus } from "../../../../../../common/Form";

interface PropType extends Omit<FormDialogProps, "children" | "handleSubmit"> {
  studyId: string;
}

function AddBindingConstDialog(props: PropType) {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();
  const { studyId, ...dialogProps } = props;
  const { onCancel } = dialogProps;
  const defaultValues: CreateBindingConstraint = {
    name: "",
    enabled: true,
    time_step: TimeStep.HOURLY,
    operator: BindingConstraintOperator.LESS,
    coeffs: {},
  };

  const handleSubmit = async (data: SubmitHandlerPlus) => {
    const { name, enabled, time_step, operator, comments } = data.dirtyValues;
    try {
      await appendCommands(studyId, [
        {
          action: CommandEnum.CREATE_BINDING_CONSTRAINT,
          args: {
            name,
            enabled: enabled !== undefined ? enabled : true,
            time_step: time_step || TimeStep.HOURLY,
            operator: operator || BindingConstraintOperator.LESS,
            coeffs: {},
            comments,
          },
        },
      ]);
      enqueueSnackbar(t("study.success.addBindingConst"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.addBindingConst"), e as AxiosError);
    } finally {
      onCancel();
    }
  };
  return (
    <FormDialog
      maxWidth="sm"
      config={{ defaultValues }}
      onSubmit={handleSubmit}
      {...dialogProps}
    >
      <AddBindingConstForm />
    </FormDialog>
  );
}

export default AddBindingConstDialog;
