import { Paper } from "@mui/material";
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
import { getBindingConstraint } from "../../../../../../../services/api/studydata";
import ConstraintFields from "./ConstraintFields";
import { BindingConstraint } from "./utils";
import { SubmitHandlerPlus } from "../../../../../../common/Form/types";

interface Props {
  constraintId: string;
}

// TODO rename ConstraintForm
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
    // TODO exclude name and id
    console.log("values", values);
    // return updateBindingConstraint(study.id, constraintId, values);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Paper
      sx={{
        display: "flex",
        flexDirection: "column",
        overflow: "auto",
        width: 1,
        height: 1,
        p: 2,
      }}
    >
      <UsePromiseCond
        response={mergeResponses(bindingConstraint, linksAndClusters)}
        ifResolved={([defaultValues, linksAndClusters]) => (
          <>
            {/* Constraint properties form */}
            <Form
              autoSubmit
              config={{ defaultValues }}
              onSubmit={handleSubmitConstraint}
            >
              <ConstraintFields study={study} />
            </Form>
            {/* Constraint terms form */}
            <Form autoSubmit config={{ defaultValues }}>
              <BindingConstForm
                study={study}
                constraintId={constraintId}
                // TODO rename: represents a constraint terms list options of areas/links.
                options={linksAndClusters}
              />
            </Form>
          </>
        )}
      />
    </Paper>
  );
}

export default BindingConstView;
