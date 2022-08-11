import { Box } from "@mui/material";
import { useFieldArray } from "react-hook-form";
import Constraint from "./Constraint";
import { AllClustersAndLinks } from "../../../../../../../../common/types";
import { getClustersAndLinks } from "../../../../../../../../services/api/studydata";
import UsePromiseCond from "../../../../../../../common/utils/UsePromiseCond";
import SimpleLoader from "../../../../../../../common/loaders/SimpleLoader";
import usePromise from "../../../../../../../../hooks/usePromise";
import { BindingConstType } from "../utils";
import NoContent from "../../../../../../../common/page/NoContent";
import { useFormContext } from "../../../../../../../common/Form";

interface Props {
  bindingConstId: string;
  studyId: string;
}

export function Constraints(props: Props) {
  const { bindingConstId, studyId } = props;
  const optionsRes = usePromise(() => getClustersAndLinks(studyId), [studyId]);
  const { control } = useFormContext<BindingConstType>();
  const { fields } = useFieldArray({
    control,
    name: "constraints",
  });
  console.log("YESSAI: ", fields);
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
        response={optionsRes}
        ifPending={() => <SimpleLoader />}
        ifResolved={(options: AllClustersAndLinks | undefined) => {
          return options ? (
            <>
              {fields.map((field, index: number) => {
                return (
                  <Constraint
                    key={field.id}
                    index={index}
                    bindingConst={bindingConstId}
                    studyId={studyId}
                    options={options}
                  />
                );
              })}
            </>
          ) : (
            <NoContent title="No constraints" />
          );
        }}
      />
    </Box>
  );
}
