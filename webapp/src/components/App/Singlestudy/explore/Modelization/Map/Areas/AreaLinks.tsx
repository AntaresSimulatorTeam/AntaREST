import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import { StudyMetadata } from "../../../../../../../common/types";
import {
  setCurrentArea,
  setCurrentLink,
} from "../../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaLinks } from "../../../../../../../redux/selectors";
import {
  AreaLinkContainer,
  AreaLinkContent,
  AreaLinkRoot,
  AreaLinkTitle,
} from "./style";

function AreaLinks() {
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaLinks = useAppSelector((state) =>
    getCurrentAreaLinks(state, study.id)
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <AreaLinkRoot>
      {areaLinks.length > 0 && (
        <AreaLinkTitle>{t("study.links")}</AreaLinkTitle>
      )}
      {areaLinks.length > 0 &&
        areaLinks.map(({ label, id }) => (
          <AreaLinkContainer key={id}>
            <AreaLinkContent
              onClick={() => {
                dispatch(setCurrentArea(""));
                dispatch(setCurrentLink(id));
              }}
            >
              {label}
            </AreaLinkContent>
          </AreaLinkContainer>
        ))}
    </AreaLinkRoot>
  );
}

export default AreaLinks;
