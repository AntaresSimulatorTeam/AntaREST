import * as R from "ramda";
import { Box } from "@mui/material";
import { useOutletContext } from "react-router";
import { LinkElement, StudyMetadata } from "../../../../../../common/types";
import usePromise, { PromiseStatus } from "../../../../../../hooks/usePromise";
import Form from "../../../../../common/Form";
import LinkForm from "./LinkForm";
import { getDefaultValues, LinkFields } from "./utils";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";

interface Props {
  link: LinkElement;
}

function LinkView(props: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { link } = props;
  const { data: defaultValues, status } = usePromise(
    () => getDefaultValues(study.id, link.area1, link.area2),
    [study.id, link.area1, link.area2]
  );

  return (
    <Box sx={{ width: "100%", height: "100%", overflowY: "auto" }}>
      {R.cond([
        [R.equals(PromiseStatus.Pending), () => <SimpleLoader />],
        [
          R.equals(PromiseStatus.Resolved),
          () => (
            <Form
              autoSubmit
              config={{ defaultValues: defaultValues as LinkFields }}
            >
              {(formObj) =>
                LinkForm({
                  ...formObj,
                  link,
                  study,
                })
              }
            </Form>
          ),
        ],
      ])(status)}
    </Box>
  );
}

export default LinkView;
