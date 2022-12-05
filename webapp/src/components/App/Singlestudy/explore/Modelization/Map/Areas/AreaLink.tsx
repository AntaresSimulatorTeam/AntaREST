import { useTranslation } from "react-i18next";
import { LinkElement } from "../../../../../../../common/types";
import {
  setCurrentArea,
  setCurrentLink,
} from "../../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";
// import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";

import {
  AreaLinkContainer,
  AreaLinkContent,
  AreaLinkRoot,
  AreaLinkTitle,
  AreaLinkLabel,
} from "./style";

interface Props {
  currentLink: LinkElement;
}

function AreaLink({ currentLink }: Props) {
  const [t] = useTranslation();
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleLinkClick = (link: string) => {
    dispatch(setCurrentLink(""));
    dispatch(setCurrentArea(link));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <AreaLinkRoot>
      <AreaLinkTitle>{t("study.links")}</AreaLinkTitle>
      <AreaLinkContainer>
        <AreaLinkLabel>{t("study.area1")}</AreaLinkLabel>
        <AreaLinkContent onClick={() => handleLinkClick(currentLink?.area1)}>
          {currentLink?.area1}
        </AreaLinkContent>
      </AreaLinkContainer>
      <AreaLinkContainer>
        <AreaLinkLabel>{t("study.area2")}</AreaLinkLabel>
        <AreaLinkContent onClick={() => handleLinkClick(currentLink?.area2)}>
          {currentLink?.area2}
        </AreaLinkContent>
      </AreaLinkContainer>
    </AreaLinkRoot>
  );
}

export default AreaLink;
