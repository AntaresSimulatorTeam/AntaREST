import { Box } from "@mui/material";
import Form from "../../../../../../../common/Form";
import { getCurrentAreaId } from "../../../../../../../../redux/selectors";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import RenewableForm from "./RenewableForm";
import { getDefaultValues } from "./utils";
import { Cluster, StudyMetadata } from "../../../../../../../../common/types";
import usePromise from "../../../../../../../../hooks/usePromise";
import SimpleLoader from "../../../../../../../common/loaders/SimpleLoader";
import UsePromiseCond from "../../../../../../../common/utils/UsePromiseCond";

interface Props {
  cluster: Cluster["id"];
  groupList: Array<string>;
  study: StudyMetadata;
}

export default function RenewableView(props: Props) {
  const { cluster, study, groupList } = props;
  const currentArea = useAppSelector(getCurrentAreaId);

  const res = usePromise(
    () => getDefaultValues(study.id, currentArea, cluster),
    [study.id, currentArea]
  );

  return (
    <Box sx={{ width: "100%", height: "100%", overflowY: "auto" }}>
      <UsePromiseCond
        response={res}
        ifPending={() => <SimpleLoader />}
        ifResolved={(data) => (
          <Form autoSubmit config={{ defaultValues: data }}>
            <RenewableForm
              study={study}
              cluster={cluster}
              area={currentArea}
              groupList={groupList}
            />
          </Form>
        )}
      />
    </Box>
  );
}
