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

interface Props extends Omit<FormDialogProps, "children" | "handleSubmit"> {
  studyId: string;
}

function AddBindingConstDialog(props: Props) {
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
    comments: "",
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus) => {
    try {
      await appendCommands(studyId, [
        {
          action: CommandEnum.CREATE_BINDING_CONSTRAINT,
          args: data.values,
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

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

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
