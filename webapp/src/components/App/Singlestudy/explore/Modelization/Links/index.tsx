import { Box } from "@mui/material";
import * as R from "ramda";
import { ReactNode } from "react";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import NoContent from "../../../../../common/page/NoContent";
import SplitLayoutView from "../../../../../common/SplitLayoutView";
import LinkPropsView from "./LinkPropsView";
import useStudyData from "../../hooks/useStudyData";
import { getCurrentLinkId, selectLinks } from "../../../../../../redux/selectors";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import { setCurrentLink } from "../../../../../../redux/ducks/studyDataSynthesis";
import LinkView from "./LinkView";

function Links() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const {
    value: studyData,
    error,
    isLoading,
  } = useStudyData({
    studyId: study.id,
    selector: selectLinks,
  });
  const currentLink = useAppSelector(getCurrentLinkId);
  const dispatch = useAppDispatch();
  const selectedLink =
    studyData && currentLink ? studyData[currentLink].name : undefined;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleLinkClick = (linkName: string): void => {
    if (studyData === undefined) return;
    const elm = studyData[linkName];
    if (elm) {
      dispatch(setCurrentLink(linkName));
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitLayoutView
      left={
        <Box width="100%" height="100%">
          {studyData !== undefined && !isLoading && (
            <LinkPropsView
              studyId={study.id}
              onClick={handleLinkClick}
              currentLink={selectedLink || undefined}
            />
          )}
        </Box>
      }
      right={
        <>
          {R.cond([
            // Loading
            [() => isLoading, () => (<SimpleLoader />) as ReactNode],
            [
              () => error !== undefined,
              () => (<NoContent title={error?.message} />) as ReactNode,
            ],
            // Link list
            [
              () => selectedLink !== undefined,
              () =>
                (
                  <Box width="100%" height="100%">
                    {studyData === undefined ? (
                      <SimpleLoader />
                    ) : (
                      <LinkView link={studyData[selectedLink as string]} />
                    )}
                  </Box>
                ) as ReactNode,
            ],
            // No Areas
            [R.T, () => (<NoContent title="No Links" />) as ReactNode],
          ])()}
        </>
      }
    />
  );
}

export default Links;
