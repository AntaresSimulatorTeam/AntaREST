import { Box } from "@mui/material";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../common/types";
import usePromise from "../../../../../../../hooks/usePromise";
import Form from "../../../../../../common/Form";
import BindingConstForm from "./BindingConstForm";
import { getDefaultValues, BindingConstFields } from "./utils";
import SimpleLoader from "../../../../../../common/loaders/SimpleLoader";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";

interface Props {
  bcIndex: number;
  bindingConst: string;
}

function BindingConstView(props: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { bindingConst, bcIndex } = props;
  const res = usePromise(
    () => getDefaultValues(study.id, bindingConst),
    [study.id, bindingConst]
  );

  return (
    <Box sx={{ width: "100%", height: "100%", overflowY: "auto" }}>
      <UsePromiseCond
        response={res}
        ifPending={() => <SimpleLoader />}
        ifResolved={(data) => (
          <Form
            autoSubmit
            config={{ defaultValues: data as BindingConstFields }}
          >
            <BindingConstForm
              study={study}
              bindingConst={bindingConst}
              bcIndex={bcIndex}
            />
          </Form>
        )}
      />
    </Box>
  );
}

export default BindingConstView;
