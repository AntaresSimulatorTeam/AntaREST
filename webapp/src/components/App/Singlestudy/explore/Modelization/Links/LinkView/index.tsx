import { useOutletContext } from "react-router";
import { LinkElement, StudyMetadata } from "../../../../../../../common/types";
import usePromise from "../../../../../../../hooks/usePromise";
import Form from "../../../../../../common/Form";
import LinkForm from "./LinkForm";
import { getDefaultValues } from "./utils";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";

interface Props {
  link: LinkElement;
}

function LinkView(props: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { link } = props;
  const res = usePromise(
    () => getDefaultValues(study.id, link.area1, link.area2),
    [study.id, link.area1, link.area2],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={res}
      ifResolved={(data) => (
        <Form autoSubmit config={{ defaultValues: data }}>
          <LinkForm link={link} study={study} />
        </Form>
      )}
    />
  );
}

export default LinkView;
