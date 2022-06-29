import * as R from "ramda";
import Form from "../../../../../../../common/Form";
import { getCurrentAreaId } from "../../../../../../../../redux/selectors";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import ThermalForm from "./ThermalForm";
import { ThermalFields } from "./utils";
import { Cluster, StudyMetadata } from "../../../../../../../../common/types";
import { getStudyData } from "../../../../../../../../services/api/study";
import usePromise, {
  PromiseStatus,
} from "../../../../../../../../hooks/usePromise";
import SimpleLoader from "../../../../../../../common/loaders/SimpleLoader";

interface Props {
  cluster: Cluster["id"];
  groupList: Array<string>;
  nameList: Array<string>;
  study: StudyMetadata;
}

export default function ThermalView(props: Props) {
  const { cluster, study, nameList, groupList } = props;
  const currentArea = useAppSelector(getCurrentAreaId);

  const { data: defaultValues, status } = usePromise(
    () =>
      getStudyData(
        study.id,
        `input/thermal/clusters/${currentArea}/list/${cluster}`,
        3
      ),
    [study.id, currentArea]
  );

  return (
    <>
      {R.cond([
        [R.equals(PromiseStatus.Pending), () => <SimpleLoader />],
        [
          R.equals(PromiseStatus.Resolved),
          () => (
            <Form
              autoSubmit
              config={{ defaultValues: defaultValues as ThermalFields }}
            >
              {(formObj) =>
                ThermalForm({
                  ...formObj,
                  study,
                  cluster,
                  area: currentArea,
                  nameList,
                  groupList,
                })
              }
            </Form>
          ),
        ],
      ])(status)}
    </>
  );
}
