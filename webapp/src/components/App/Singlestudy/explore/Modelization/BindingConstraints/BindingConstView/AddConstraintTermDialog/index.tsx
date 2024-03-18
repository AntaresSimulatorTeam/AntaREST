import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { UseFieldArrayAppend } from "react-hook-form";
import FormDialog, {
  FormDialogProps,
} from "../../../../../../../common/dialogs/FormDialog";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import {
  BindingConstraint,
  ConstraintTerm,
  dataToId,
  isDataLink,
  isOptionExist,
  isTermExist,
} from "../utils";
import AddConstraintTermForm from "./AddConstraintTermForm";
import { addConstraintTerm } from "../../../../../../../../services/api/studydata";
import {
  AllClustersAndLinks,
  ClusterElement,
  LinkCreationInfoDTO,
} from "../../../../../../../../common/types";
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
  const defaultValues: ConstraintTerm = {
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

  const handleSubmit = async (values: SubmitHandlerPlus) => {
    try {
      const tmpValues = values.dirtyValues as ConstraintTerm;
      const isLink = isDataLink(tmpValues.data);
      if (tmpValues.weight === undefined) {
        tmpValues.weight = 0.0;
      }
      let data: LinkCreationInfoDTO | ClusterElement;
      // Verify if this link/cluster combination is allowed
      if (isLink) {
        data = tmpValues.data as LinkCreationInfoDTO;
        if (!isOptionExist(options.links, data.area1, data.area2)) {
          enqueueSnackbar(
            t("study.error.missingData", {
              0: t("study.area1"),
              1: t("study.area2"),
            }),
            { variant: "error" },
          );
          onCancel();
          return;
        }
      } else {
        data = tmpValues.data as ClusterElement;
        if (!isOptionExist(options.clusters, data.area, data.cluster)) {
          enqueueSnackbar(
            t("study.error.missingData", {
              0: t("study.area"),
              1: t("study.cluster"),
            }),
            { variant: "error" },
          );
          onCancel();
          return;
        }
      }

      // Verify if this term already exist in current term list
      const termId = dataToId(data);
      if (isTermExist(constraintTerms, termId)) {
        enqueueSnackbar(t("study.error.termAlreadyExist"), {
          variant: "error",
        });
        onCancel();
        return;
      }

      // Send
      await addConstraintTerm(
        studyId,
        constraintId,
        values.dirtyValues as ConstraintTerm,
      );

      // Add to current UX
      append(tmpValues as ConstraintTerm);
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
