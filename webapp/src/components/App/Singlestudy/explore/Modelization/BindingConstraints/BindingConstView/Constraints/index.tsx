import { Box } from "@mui/material";
import { useMemo } from "react";
import { useFormContext } from "../../../../../../../common/Form";
import { BindingConstFields, getContraintsValues } from "../utils";
import Constraint from "./Constraint";

interface Props {
  bindingConst: string;
  studyId: string;
}

export function Constraints(props: Props) {
  const { defaultValues } = useFormContext<BindingConstFields>();
  const { bindingConst, studyId } = props;
  const constraints = useMemo(
    () => getContraintsValues(defaultValues as Partial<BindingConstFields>),
    [defaultValues]
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
      {Object.keys(constraints).map((key, index) => {
        return (
          <Constraint
            key={key}
            constraint={constraints[key]}
            fieldset={index > 0}
            bindingConst={bindingConst}
            studyId={studyId}
          />
        );
      })}
    </Box>
  );
}
