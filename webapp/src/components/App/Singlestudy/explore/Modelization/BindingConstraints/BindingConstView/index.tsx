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
  bindingConst: string;
}

function BindingConstView(props: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { bindingConst } = props;
  const defaultValuesRes = usePromise(
    () => getDefaultValues(study.id, bindingConst),
    [study.id, bindingConst]
  );
  const optionsRes = useStudySynthesis({
    studyId: study.id,
    selector: (state) => getLinksAndClusters(state, study.id),
  });

  return (
    <Box sx={{ width: 1, height: 1, overflowY: "auto" }}>
      <Paper sx={{ width: 1, height: 1, padding: 2, overflow: "auto" }}>
        <UsePromiseCond
          response={mergeResponses(defaultValuesRes, optionsRes)}
          ifResolved={([defaultValues, options]) => (
            <Form autoSubmit config={{ defaultValues }}>
              {bindingConst && (
                <BindingConstForm
                  study={study}
                  bindingConst={bindingConst}
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
