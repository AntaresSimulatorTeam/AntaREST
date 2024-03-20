import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { UseFieldArrayAppend } from "react-hook-form";
import FormDialog, {
  FormDialogProps,
} from "../../../../../../../common/dialogs/FormDialog";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import { BindingConstraint } from "../utils";
import AddConstraintTermForm from "./AddConstraintTermForm";
import { addConstraintTerm } from "../../../../../../../../services/api/studydata";
import { AllClustersAndLinks } from "../../../../../../../../common/types";
import useStudySynthesis from "../../../../../../../../redux/hooks/useStudySynthesis";
import { getLinksAndClusters } from "../../../../../../../../redux/selectors";

interface Props extends Omit<FormDialogProps, "children" | "handleSubmit"> {
  studyId: string;
  constraintId: string;
  append: UseFieldArrayAppend<BindingConstraint, "constraints">;
  constraintTerms: BindingConstraint["constraints"];
  options: AllClustersAndLinks;
}

function AddConstraintTermDialog(props: Props) {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();
  const {
    studyId,
    constraintId,
    options,
    constraintTerms,
    append,
    ...dialogProps
  } = props;
  const { onCancel } = dialogProps;
  const defaultValues = {
    id: "",
    weight: 0,
    offset: 0,
    data: {
      area1: "",
      area2: "",
    },
  };
  const { data: optionsItems } = useStudySynthesis({
    studyId,
    selector: (state) => getLinksAndClusters(state, studyId),
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  // TODO fix type
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleSubmit = async ({ values }: SubmitHandlerPlus<any>) => {
    try {
      await addConstraintTerm(studyId, constraintId, values);

      append(values);
      enqueueSnackbar(t("study.success.addConstraintTerm"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.addConstraintTerm"), e as AxiosError);
    } finally {
      onCancel();
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      maxWidth="md"
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
