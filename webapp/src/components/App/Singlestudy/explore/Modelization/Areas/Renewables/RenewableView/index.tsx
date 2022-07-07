import * as R from "ramda";
import Form from "../../../../../../../common/Form";
import { getCurrentAreaId } from "../../../../../../../../redux/selectors";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import RenewableForm from "./RenewableForm";
import { getDefaultValues, RenewableFields } from "./utils";
import { Cluster, StudyMetadata } from "../../../../../../../../common/types";
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

export default function RenewableView(props: Props) {
  const { cluster, study, nameList, groupList } = props;
  const currentArea = useAppSelector(getCurrentAreaId);

  const { data: defaultValues, status } = usePromise(
    () => getDefaultValues(study.id, currentArea, cluster),
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
              config={{ defaultValues: defaultValues as RenewableFields }}
            >
              <RenewableForm
                study={study}
                cluster={cluster}
                area={currentArea}
                nameList={nameList}
                groupList={groupList}
              />
            </Form>
          ),
        ],
      ])(status)}
    </>
  );
}
