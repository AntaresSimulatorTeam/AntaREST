/* eslint-disable camelcase */
import { Box, Button } from "@mui/material";
import { useEffect, useMemo } from "react";
import { useFieldArray } from "react-hook-form";
import Constraint from "./Constraint";
import { AllClustersAndLinks } from "../../../../../../../../common/types";
import {
  // addConstraintTerm,
  getClustersAndLinks,
} from "../../../../../../../../services/api/studydata";
import UsePromiseCond from "../../../../../../../common/utils/UsePromiseCond";
import SimpleLoader from "../../../../../../../common/loaders/SimpleLoader";
import usePromise from "../../../../../../../../hooks/usePromise";
import { BindingConstFields, ConstraintType } from "../utils";
import NoContent from "../../../../../../../common/page/NoContent";
import { useFormContext } from "../../../../../../../common/Form";

interface Props {
  bindingConstId: string;
  studyId: string;
}

export function Constraints(props: Props) {
  const { bindingConstId, studyId } = props;
  const optionsRes = usePromise(() => getClustersAndLinks(studyId), [studyId]);

  const { control, defaultValues } = useFormContext<BindingConstFields>();
  const { fields } = useFieldArray({
    control,
    name: "constraints",
  });

  const values = useMemo(
    () =>
      defaultValues as Required<
        Omit<BindingConstFields, "comments"> & { comments?: string }
      >,
    [defaultValues]
  );

  console.log("AAAAAAAAAH");

  useEffect(() => {
    console.log("FIELDS: ", fields);
  }, [fields]);

  useEffect(() => {
    console.log("VALUES: ", values);
  }, [values]);

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
              <Box
                sx={{
                  width: "100%",
                  display: "flex",
                  justifyContent: "flex-end",
                  alignItems: "center",
                }}
              >
                <Button variant="text" color="primary">
                  Add constraint term
                </Button>
              </Box>
              {fields.map((field, index: number) => {
                const constraint: ConstraintType = values.constraints[index];
                return (
                  <Constraint
                    key={field.id}
                    index={index}
                    constraint={constraint as ConstraintType}
                    bindingConst={bindingConstId}
                    studyId={studyId}
                    options={options}
                    control={control}
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
