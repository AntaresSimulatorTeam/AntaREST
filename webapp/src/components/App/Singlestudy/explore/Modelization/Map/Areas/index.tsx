import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { StudyMetadata, UpdateAreaUi } from "../../../../../../../common/types";
import PropertiesView from "../../../../../../common/PropertiesView";
import ListElement from "../../../common/ListElement";
import { AreasContainer } from "./style";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import {
  getCurrentLink,
  getCurrentStudyMapNode,
} from "../../../../../../../redux/selectors";
import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";
import AreaConfig from "./AreaConfig";
import { isSearchMatching } from "../../../../../../../utils/stringUtils";
import { setCurrentArea } from "../../../../../../../redux/ducks/studySyntheses";
import { StudyMapNode } from "../../../../../../../redux/ducks/studyMaps";

interface Props {
  onAdd: () => void;
  updateUI: (id: string, value: UpdateAreaUi) => void;
  nodes: StudyMapNode[];
}

function Areas({ onAdd, updateUI, nodes }: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();
  const [filteredNodes, setFilteredNodes] = useState<StudyMapNode[]>([]);
  const [searchValue, setSearchValue] = useState("");
  const [showAreaConfig, setShowAreaConfig] = useState(false);
  const currentArea = useAppSelector(getCurrentStudyMapNode);
  const currentLink = useAppSelector((state) =>
    getCurrentLink(state, study.id),
  );

  useEffect(() => {
    setFilteredNodes(
      nodes.filter(({ id }) => isSearchMatching(searchValue, id)),
    );
  }, [nodes, searchValue]);

  useEffect(() => {
    setShowAreaConfig(!!(currentArea || currentLink));
  }, [currentArea, currentLink]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <PropertiesView
      mainContent={
        showAreaConfig && (
          <AreasContainer>
            <AreaConfig
              currentArea={currentArea}
              updateUI={updateUI}
              currentLink={currentLink}
            />
          </AreasContainer>
        )
      }
      secondaryContent={
        (!showAreaConfig || (!currentArea && !currentLink)) &&
        filteredNodes.length > 0 && (
          <ListElement
            setSelectedItem={({ id }) => {
              dispatch(setCurrentArea(id));
              setShowAreaConfig(true);
            }}
            list={filteredNodes}
          />
        )
      }
      onSearchFilterChange={(searchValue) => {
        setSearchValue(searchValue);
      }}
      onAdd={onAdd}
    />
  );
}

export default Areas;
