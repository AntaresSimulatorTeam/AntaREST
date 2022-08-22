/* eslint-disable camelcase */
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { UseFieldArrayAppend } from "react-hook-form";
import FormDialog, {
  FormDialogProps,
} from "../../../../../../../common/dialogs/FormDialog";
import { SubmitHandlerPlus } from "../../../../../../../common/Form";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import { BindingConstType, ConstraintType } from "../utils";
import AddConstraintTermForm from "./AddConstraintTermForm";
import UsePromiseCond from "../../../../../../../common/utils/UsePromiseCond";
import SimpleLoader from "../../../../../../../common/loaders/SimpleLoader";
import {
  addConstraintTerm,
  getClustersAndLinks,
} from "../../../../../../../../services/api/studydata";
import usePromise from "../../../../../../../../hooks/usePromise";

interface PropType extends Omit<FormDialogProps, "children" | "handleSubmit"> {
  studyId: string;
  bindingConstraint: string;
  append: UseFieldArrayAppend<BindingConstType, "constraints">;
}

function AddConstraintTermDialog(props: PropType) {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();
  const { studyId, bindingConstraint, append, ...dialogProps } = props;
  const { onCancel } = dialogProps;
  const defaultValues: ConstraintType = {
    id: "",
    weight: 0,
    offset: 0,
    data: {
      area1: "",
      area2: "",
    },
  };
  const optionsRes = usePromise(() => getClustersAndLinks(studyId), [studyId]);

  const handleSubmit = async (values: SubmitHandlerPlus) => {
    try {
      /*  */
      await addConstraintTerm(
        studyId,
        bindingConstraint,
        values.dirtyValues as ConstraintType
      );
      append(values.dirtyValues as ConstraintType);
      enqueueSnackbar(t("study.success.addConstraintTerm"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.addConstraintTerm"), e as AxiosError);
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
      <UsePromiseCond
        response={optionsRes}
        ifPending={() => <SimpleLoader />}
        ifResolved={(options) =>
          options && <AddConstraintTermForm options={options} />
        }
      />
    </FormDialog>
  );
}

export default AddConstraintTermDialog;
