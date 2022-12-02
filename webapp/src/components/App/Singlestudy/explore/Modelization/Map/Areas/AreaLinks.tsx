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
} from "../style";

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
      {areaLinks && areaLinks.length >= 1 && (
        <AreaLinkTitle>{t("study.links")}</AreaLinkTitle>
      )}
      {areaLinks &&
        areaLinks.map(({ area1, area2 }) => (
          <AreaLinkContainer key={`${area1}${area2}`}>
            <AreaLinkContent
              onClick={() => {
                dispatch(setCurrentArea(""));
                dispatch(setCurrentLink(`${area1} / ${area2}`));
              }}
            >
              {area1} / {area2}
            </AreaLinkContent>
          </AreaLinkContainer>
        ))}
    </AreaLinkRoot>
  );
}

export default AreaLinks;
