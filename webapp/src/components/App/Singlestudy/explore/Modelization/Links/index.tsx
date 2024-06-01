import { Box } from "@mui/material";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import SimpleContent from "../../../../../common/page/SimpleContent";
import LinkPropsView from "./LinkPropsView";
import useStudySynthesis from "../../../../../../redux/hooks/useStudySynthesis";
import { getCurrentLink } from "../../../../../../redux/selectors";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import { setCurrentLink } from "../../../../../../redux/ducks/studySyntheses";
import LinkView from "./LinkView";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import SplitView from "../../../../../common/SplitView";

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
    <SplitView sizes={[10, 90]}>
      <Box width="100%" height="100%">
        <LinkPropsView studyId={study.id} onClick={handleLinkClick} />
      </Box>
      <Box>
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
      </Box>
    </SplitView>
  );
}

export default Links;
