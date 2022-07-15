import { Box } from "@mui/material";
import { useOutletContext } from "react-router";
import { LinkElement, StudyMetadata } from "../../../../../../../common/types";
import usePromise from "../../../../../../../hooks/usePromise";
import Form from "../../../../../../common/Form";
import LinkForm from "./LinkForm";
import { getDefaultValues } from "./utils";
import SimpleLoader from "../../../../../../common/loaders/SimpleLoader";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";

interface Props {
  link: LinkElement;
}

function LinkView(props: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { link } = props;
  const res = usePromise(
    () => getDefaultValues(study.id, link.area1, link.area2),
    [study.id, link.area1, link.area2]
  );

  return (
    <Box sx={{ width: "100%", height: "100%", overflowY: "auto" }}>
      <UsePromiseCond
        response={res}
        ifPending={() => <SimpleLoader />}
        ifResolved={(data) => (
          <Form autoSubmit config={{ defaultValues: data }}>
            {(formObj) =>
              LinkForm({
                ...formObj,
                link,
                study,
              })
            }
          </Form>
        )}
      />
    </Box>
  );
}

export default LinkView;
