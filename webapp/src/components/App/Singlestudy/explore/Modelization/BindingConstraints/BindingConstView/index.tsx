import { Box, Paper } from "@mui/material";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../common/types";
import usePromise from "../../../../../../../hooks/usePromise";
import Form from "../../../../../../common/Form";
import BindingConstForm from "./BindingConstForm";
import UsePromiseCond, {
  mergeResponses,
} from "../../../../../../common/utils/UsePromiseCond";
import useStudySynthesis from "../../../../../../../redux/hooks/useStudySynthesis";
import { getLinksAndClusters } from "../../../../../../../redux/selectors";
import {
  getBindingConstraint,
  updateBindingConstraint,
} from "../../../../../../../services/api/studydata";
import ConstraintFields from "./ConstraintFields";
import { SubmitHandlerPlus } from "../../../../../../common/Form/types";
import { BindingConstraint } from "./utils";

interface Props {
  constraintId: string;
}

// TODO rename Form (its the constraint form => properties + terms forms)
function BindingConstView({ constraintId }: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  const bindingConstraint = usePromise(
    () => getBindingConstraint(study.id, constraintId),
    [study.id, constraintId],
  );

  const linksAndClusters = useStudySynthesis({
    studyId: study.id,
    selector: (state) => getLinksAndClusters(state, study.id),
  });

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmitConstraint = ({
    values,
  }: SubmitHandlerPlus<BindingConstraint>) => {
    const { id, name, constraints, ...updatedConstraint } = values;

    return updateBindingConstraint(study.id, constraintId, updatedConstraint);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Paper
      sx={{
        p: 2,
        width: 1,
        height: 1,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <UsePromiseCond
        response={mergeResponses(bindingConstraint, linksAndClusters)}
        ifResolved={([defaultValues, linksAndClusters]) => (
          <>
            <Box sx={{ display: "flex", width: 1 }}>
              <Form
                autoSubmit
                config={{ defaultValues }}
                onSubmit={handleSubmitConstraint}
                sx={{ flexGrow: 1 }}
              >
                <ConstraintFields study={study} />
              </Form>
            </Box>

            <Box sx={{ display: "flex", flexGrow: 1 }}>
              <Form autoSubmit config={{ defaultValues }} sx={{ flexGrow: 1 }}>
                <BindingConstForm
                  study={study}
                  constraintId={constraintId}
                  // TODO rename options => represents a constraint terms list options of areas/links.
                  options={linksAndClusters}
                />
              </Form>
            </Box>
          </>
        )}
      />
    </Paper>
  );
}

export default BindingConstView;
