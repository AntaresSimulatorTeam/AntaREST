import { Box } from "@mui/material";
import * as R from "ramda";
import { useOutletContext } from "react-router";
import { LinkElement, StudyMetadata } from "../../../../../../common/types";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import SimpleContent from "../../../../../common/page/SimpleContent";
import SplitLayoutView from "../../../../../common/SplitLayoutView";
import LinkPropsView from "./LinkPropsView";
import useStudySynthesis from "../../../../../../redux/hooks/useStudySynthesis";
import { getCurrentLink } from "../../../../../../redux/selectors";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import { setCurrentLink } from "../../../../../../redux/ducks/studySyntheses";
import LinkView from "./LinkView";

function Links() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { error, isLoading } = useStudySynthesis({ studyId: study.id });
  const currentLink = useAppSelector((state) =>
    getCurrentLink(state, study.id)
  );
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleLinkClick = (linkName: string): void => {
    dispatch(setCurrentLink(linkName));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitLayoutView
      left={
        <Box width="100%" height="100%">
          <LinkPropsView
            studyId={study.id}
            onClick={handleLinkClick}
            currentLink={currentLink?.name}
          />
        </Box>
      }
      right={
        <>
          {R.cond([
            // Loading
            [() => isLoading, () => <SimpleLoader />],
            // Error
            [
              () => error !== undefined,
              () => <SimpleContent title={error?.message} />,
            ],
            // Link list
            [
              () => !!currentLink,
              () => (
                <Box width="100%" height="100%">
                  <LinkView link={currentLink as LinkElement} />
                </Box>
              ),
            ],
            // No Areas
            [R.T, () => <SimpleContent title="No Links" />],
          ])()}
        </>
      }
    />
  );
}

export default Links;
