import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { UseFieldArrayAppend } from "react-hook-form";
import FormDialog, {
  FormDialogProps,
} from "../../../../../../../common/dialogs/FormDialog";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import { type BindingConstraint, type ConstraintTerm } from "../utils";
import AddConstraintTermForm from "./AddConstraintTermForm";
import { createConstraintTerm } from "../../../../../../../../services/api/studydata";
import { AllClustersAndLinks } from "../../../../../../../../common/types";
import useStudySynthesis from "../../../../../../../../redux/hooks/useStudySynthesis";
import { getLinksAndClusters } from "../../../../../../../../redux/selectors";
import { BaseSyntheticEvent } from "react";

interface Props extends Omit<FormDialogProps, "children" | "handleSubmit"> {
  studyId: string;
  constraintId: string;
  append: UseFieldArrayAppend<BindingConstraint, "constraints">;
  constraintTerms: ConstraintTerm[];
  options: AllClustersAndLinks;
}

const defaultValues = {
  id: "",
  weight: 0,
  offset: undefined,
  data: {
    area1: "",
    area2: "",
  },
} as const;

function AddConstraintTermDialog({
  studyId,
  constraintId,
  options,
  constraintTerms,
  append,
  ...dialogProps
}: Props) {
  const [t] = useTranslation();
  const { onCancel } = dialogProps;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const { data: optionsItems } = useStudySynthesis({
    studyId,
    selector: (state) => getLinksAndClusters(state, studyId),
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (
    { values }: SubmitHandlerPlus<Record<string, unknown>>,
    _event?: BaseSyntheticEvent,
  ) => {
    try {
      const constraintTermValues = values as unknown as ConstraintTerm;

      await createConstraintTerm(studyId, constraintId, constraintTermValues);

      append(constraintTermValues);

      enqueueSnackbar(t("study.success.createConstraintTerm"), {
        variant: "success",
        autoHideDuration: 2000,
      });
    } catch (e) {
      enqueueErrorSnackbar(
        t("study.error.createConstraintTerm"),
        e as AxiosError,
      );
    } finally {
      onCancel();
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      maxWidth="lg"
      config={{ defaultValues }}
      onSubmit={handleSubmit}
      {...dialogProps}
    >
      {optionsItems && (
        <AddConstraintTermForm
          options={optionsItems}
          constraintTerms={constraintTerms}
        />
      )}
    </FormDialog>
  );
}

export default AddConstraintTermDialog;
