import { useTranslation } from "react-i18next";
import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import {
  AreaLinkContainer,
  AreaLinkContent,
  AreaLinkRoot,
  AreaLinkTitle,
  AreaLinkLabel,
} from "../style";

function AreaLink() {
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const mapNodes = useAppSelector(getMapNodes);
  const selectedLink = useAppSelector(getSelectedLink);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleLinkClick = (link: string | undefined) => {
    if (mapNodes) {
      const selectedNode = mapNodes.find((node) => node.id === link);
      dispatch(setSelectedLink(undefined));
      dispatch(setSelectedNode(selectedNode));
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <AreaLinkRoot>
      <AreaLinkTitle>{t("study.links")}</AreaLinkTitle>
      <AreaLinkContainer>
        <AreaLinkLabel>{t("study.area1")}</AreaLinkLabel>
        <AreaLinkContent onClick={() => handleLinkClick(selectedLink?.source)}>
          {selectedLink?.source}
        </AreaLinkContent>
      </AreaLinkContainer>
      <AreaLinkContainer>
        <AreaLinkLabel>{t("study.area2")}</AreaLinkLabel>
        <AreaLinkContent onClick={() => handleLinkClick(selectedLink?.target)}>
          {selectedLink?.target}
        </AreaLinkContent>
      </AreaLinkContainer>
    </AreaLinkRoot>
  );
}

export default AreaLink;
