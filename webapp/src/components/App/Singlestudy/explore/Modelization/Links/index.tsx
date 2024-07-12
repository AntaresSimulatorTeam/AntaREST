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
import ViewWrapper from "../../../../../common/page/ViewWrapper";

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
    <SplitView id="links" sizes={[10, 90]}>
      {/* Left */}
      <LinkPropsView studyId={study.id} onClick={handleLinkClick} />
      {/* Right */}
      <ViewWrapper>
        <UsePromiseCond
          response={res}
          ifResolved={(currentLink) =>
            currentLink ? (
              <LinkView link={currentLink} />
            ) : (
              <SimpleContent title="No Links" />
            )
          }
        />
      </ViewWrapper>
    </SplitView>
  );
}

export default Links;
