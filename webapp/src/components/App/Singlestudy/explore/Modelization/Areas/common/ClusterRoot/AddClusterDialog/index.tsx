import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { AddClustersFields, ClusterList } from "../utils";
import FormDialog, {
  FormDialogProps,
} from "../../../../../../../../common/dialogs/FormDialog";
import AddClusterForm from "./AddClusterForm";
import { SubmitHandlerData } from "../../../../../../../../common/Form";
import useEnqueueErrorSnackbar from "../../../../../../../../../hooks/useEnqueueErrorSnackbar";
import { appendCommands } from "../../../../../../../../../services/api/variant";
import { CommandEnum } from "../../../../../../Commands/Edition/commandTypes";

interface PropType extends Omit<FormDialogProps, "children" | "handleSubmit"> {
  clusterData: ClusterList | undefined;
  clusterGroupList: Array<string>;
  studyId: string;
  area: string;
  type: "thermals" | "renewables";
}

function AddClusterDialog(props: PropType) {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();
  const { type, clusterGroupList, clusterData, studyId, area, ...dialogProps } =
    props;
  const { onCancel } = dialogProps;
  const defaultValues: AddClustersFields = {
    name: "",
    group: "",
  };

  const handleSubmit = async (data: SubmitHandlerData) => {
    const { name, group } = data.dirtyValues;
    try {
      await appendCommands(studyId, [
        {
          action:
            type === "thermals"
              ? CommandEnum.CREATE_CLUSTER
              : CommandEnum.CREATE_RENEWABLES_CLUSTER,
          args: {
            area_id: area,
            cluster_name: (name as string).toLowerCase(),
            parameters: {
              group: group || "*",
            },
          },
        },
      ]);
      enqueueSnackbar(t("study.success.addCluster"), { variant: "success" });
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.addCluster"), e as AxiosError);
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
      {(formObj) =>
        AddClusterForm({
          ...formObj,
          clusterGroupList,
        })
      }
    </FormDialog>
  );
}

export default AddClusterDialog;
