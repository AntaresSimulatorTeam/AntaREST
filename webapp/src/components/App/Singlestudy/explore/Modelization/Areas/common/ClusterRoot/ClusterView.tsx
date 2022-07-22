import { Box } from "@mui/material";
import { DeepPartial, FieldValues, UnpackNestedValue } from "react-hook-form";
import { PropsWithChildren } from "react";
import Form from "../../../../../../../common/Form";
import { Cluster, StudyMetadata } from "../../../../../../../../common/types";
import usePromise from "../../../../../../../../hooks/usePromise";
import SimpleLoader from "../../../../../../../common/loaders/SimpleLoader";
import UsePromiseCond from "../../../../../../../common/utils/UsePromiseCond";

interface ClusterViewProps<T> {
  area: string;
  cluster: Cluster["id"];
  studyId: StudyMetadata["id"];
  getDefaultValues: (
    studyId: StudyMetadata["id"],
    area: string,
    cluster: string
  ) => Promise<T>;
}

export default function ClusterView<T extends FieldValues>(
  props: PropsWithChildren<ClusterViewProps<T>>
) {
  const { area, getDefaultValues, cluster, studyId, children } = props;

  const res = usePromise(
    () => getDefaultValues(studyId, area, cluster),
    [studyId, area]
  );

  return (
    <Box sx={{ width: "100%", height: "100%", overflowY: "auto" }}>
      <UsePromiseCond
        response={res}
        ifPending={() => <SimpleLoader />}
        ifResolved={(data) => (
          <Form
            autoSubmit
            config={{
              defaultValues: data as
                | UnpackNestedValue<DeepPartial<T>>
                | undefined,
            }}
          >
            {children}
          </Form>
        )}
      />
    </Box>
  );
}
