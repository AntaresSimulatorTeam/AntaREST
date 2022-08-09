import { Box } from "@mui/material";
import { useState } from "react";
import Constraint from "./Constraint";
import { AllClustersAndLinks } from "../../../../../../../../common/types";
import {
  getBindingConstraint,
  getClustersAndLinks,
} from "../../../../../../../../services/api/studydata";
import UsePromiseCond from "../../../../../../../common/utils/UsePromiseCond";
import SimpleLoader from "../../../../../../../common/loaders/SimpleLoader";
import usePromise from "../../../../../../../../hooks/usePromise";
import { BindingConstType } from "../utils";
import NoContent from "../../../../../../../common/page/NoContent";

interface Props {
  bindingConstId: string;
  studyId: string;
}

export function Constraints(props: Props) {
  const { bindingConstId, studyId } = props;
  const optionsRes = usePromise(() => getClustersAndLinks(studyId), [studyId]);

  const [refresh, setRefresh] = useState<number>(0);
  const bcRes = usePromise(
    async () => getBindingConstraint(studyId, bindingConstId),
    [bindingConstId, studyId, refresh]
  );

  return (
    <Box
      sx={{
        display: "flex",
        width: "100%",
        flexDirection: "column",
        mb: 1,
      }}
    >
      <UsePromiseCond
        response={bcRes}
        ifPending={() => <SimpleLoader />}
        ifResolved={(data: Omit<BindingConstType, "name"> | undefined) => (
          <UsePromiseCond
            response={optionsRes}
            ifPending={() => <SimpleLoader />}
            ifResolved={(options: AllClustersAndLinks | undefined) => {
              return data && data.constraints && options ? (
                <>
                  {Object.keys(data.constraints).map((key, index) => {
                    return (
                      <Constraint
                        key={key}
                        constraint={data.constraints[key]}
                        fieldset={index > 0}
                        bindingConst={bindingConstId}
                        studyId={studyId}
                        options={options}
                        onUpdate={() => setRefresh((r) => r + 1)}
                      />
                    );
                  })}
                </>
              ) : (
                <NoContent title="No constraints" />
              );
            }}
          />
        )}
      />
    </Box>
  );
}
