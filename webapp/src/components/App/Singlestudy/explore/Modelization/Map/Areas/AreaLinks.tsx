import { useTranslation } from "react-i18next";
import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import {
  AreaLinkContainer,
  AreaLinkContent,
  AreaLinkRoot,
  AreaLinkTitle,
} from "../style";

function AreaLinks() {
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const selectedNodeLinks = useAppSelector(getSelectedNodeLinks);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <AreaLinkRoot>
      {selectedNodeLinks.length >= 1 && (
        <AreaLinkTitle>{t("study.links")}</AreaLinkTitle>
      )}
      {selectedNodeLinks &&
        selectedNodeLinks.map(({ source, target }) => (
          <AreaLinkContainer key={`${source}${target}`}>
            <AreaLinkContent
              onClick={() => {
                dispatch(setSelectedNode(undefined));
                dispatch(setSelectedLink({ source, target }));
              }}
            >
              {source} / {target}
            </AreaLinkContent>
          </AreaLinkContainer>
        ))}
    </AreaLinkRoot>
  );
}

export default AreaLinks;
