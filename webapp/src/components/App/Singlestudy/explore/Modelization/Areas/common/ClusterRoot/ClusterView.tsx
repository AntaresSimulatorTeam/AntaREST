import { Box } from "@mui/material";
import { DeepPartial, FieldValues } from "react-hook-form";
import { PropsWithChildren } from "react";
import Form from "../../../../../../../common/Form";
import { Cluster, StudyMetadata } from "../../../../../../../../common/types";
import usePromise from "../../../../../../../../hooks/usePromise";
import UsePromiseCond from "../../../../../../../common/utils/UsePromiseCond";

interface ClusterViewProps<T> {
  area: string;
  cluster: Cluster["id"];
  studyId: StudyMetadata["id"];
  noDataValues: Partial<T>;
  type: "thermals" | "renewables";
  getDefaultValues: (
    studyId: StudyMetadata["id"],
    area: string,
    cluster: string,
    noDataValues: Partial<T>,
    type: "thermals" | "renewables"
  ) => Promise<T>;
}

export default function ClusterView<T extends FieldValues>(
  props: PropsWithChildren<ClusterViewProps<T>>
) {
  const {
    area,
    getDefaultValues,
    cluster,
    studyId,
    noDataValues,
    type,
    children,
  } = props;

  const res = usePromise(
    () => getDefaultValues(studyId, area, cluster, noDataValues, type),
    [studyId, area]
  );

  return (
    <Box sx={{ width: "100%", height: "100%", overflowY: "auto" }}>
      <UsePromiseCond
        response={res}
        ifResolved={(data) => (
          <Form
            autoSubmit
            config={{
              defaultValues: data as DeepPartial<T>,
            }}
          >
            {children}
          </Form>
        )}
      />
    </Box>
  );
}
