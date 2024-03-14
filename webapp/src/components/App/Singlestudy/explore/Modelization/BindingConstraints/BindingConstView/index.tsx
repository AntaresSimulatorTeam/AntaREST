import { Box, Paper } from "@mui/material";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../common/types";
import usePromise from "../../../../../../../hooks/usePromise";
import Form from "../../../../../../common/Form";
import BindingConstForm from "./BindingConstForm";
import { getDefaultValues } from "./utils";
import UsePromiseCond, {
  mergeResponses,
} from "../../../../../../common/utils/UsePromiseCond";
import useStudySynthesis from "../../../../../../../redux/hooks/useStudySynthesis";
import { getLinksAndClusters } from "../../../../../../../redux/selectors";

interface Props {
  constraintId: string;
}

function BindingConstView({ constraintId }: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  const defaultValuesRes = usePromise(
    () => getDefaultValues(study.id, constraintId),
    [study.id, constraintId],
  );

  const optionsRes = useStudySynthesis({
    studyId: study.id,
    selector: (state) => getLinksAndClusters(state, study.id),
  });

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ width: 1, height: 1, overflowY: "auto" }}>
      <Paper sx={{ width: 1, height: 1, pt: 1, p: 2, overflow: "auto" }}>
        <UsePromiseCond
          response={mergeResponses(defaultValuesRes, optionsRes)}
          ifResolved={([defaultValues, options]) => (
            <Form autoSubmit config={{ defaultValues }}>
              {constraintId && (
                <BindingConstForm
                  study={study}
                  constraintId={constraintId}
                  options={options}
                />
              )}
            </Form>
          )}
        />
      </Paper>
    </Box>
  );
}

export default BindingConstView;
