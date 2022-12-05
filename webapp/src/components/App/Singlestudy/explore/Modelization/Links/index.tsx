import { Box } from "@mui/material";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import SimpleContent from "../../../../../common/page/SimpleContent";
import SplitLayoutView from "../../../../../common/SplitLayoutView";
import LinkPropsView from "./LinkPropsView";
import useStudySynthesis from "../../../../../../redux/hooks/useStudySynthesis";
import { getCurrentLink } from "../../../../../../redux/selectors";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import { setCurrentLink } from "../../../../../../redux/ducks/studySyntheses";
import LinkView from "./LinkView";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";

function Links() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const res = useStudySynthesis({
    studyId: study.id,
    selector: getCurrentLink,
  });

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
          <LinkPropsView studyId={study.id} onClick={handleLinkClick} />
        </Box>
      }
      right={
        <UsePromiseCond
          response={res}
          ifResolved={(currentLink) =>
            currentLink ? (
              <Box sx={{ width: 1, height: 1 }}>
                <LinkView link={currentLink} />
              </Box>
            ) : (
              <SimpleContent title="No Links" />
            )
          }
        />
      }
    />
  );
}

export default Links;
