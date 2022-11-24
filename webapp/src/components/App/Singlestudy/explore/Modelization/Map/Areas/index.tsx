import { useEffect, useState } from "react";
import {
  NodeProperties,
  UpdateAreaUi,
} from "../../../../../../../common/types";
import PropertiesView from "../../../../../../common/PropertiesView";
import ListElement from "../../../common/ListElement";
import { AreasContainer } from "../style";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import {
  getCurrentAreaId,
  getMapNodes,
  getSelectedLink,
  getSelectedNode,
} from "../../../../../../../redux/selectors";
import { setSelectedNode } from "../../../../../../../redux/ducks/studyDataSynthesis";
import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";
import AreaConfig from "./AreaConfig";
import { isSearchMatching } from "../../../../../../../utils/textUtils";

interface Props {
  onAdd: () => void;
  updateUI: (id: string, value: UpdateAreaUi) => void;
}

function Areas(props: Props) {
  const { onAdd, updateUI } = props;
  const dispatch = useAppDispatch();
  const mapNodes = useAppSelector(getMapNodes);
  const selectedNode = useAppSelector(getSelectedNode);
  const selectedLink = useAppSelector(getSelectedLink);
  const currentNode = useAppSelector(getCurrentAreaId);
  const [filteredNodes, setFilteredNodes] = useState<Array<NodeProperties>>([]);
  const [searchValue, setSearchValue] = useState("");

  useEffect(() => {
    const filter = (): NodeProperties[] => {
      if (mapNodes) {
        return mapNodes.filter((node) =>
          isSearchMatching(searchValue, node.id)
        );
      }
      return [];
    };

    setFilteredNodes(filter());
  }, [mapNodes, searchValue]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <PropertiesView
      mainContent={
        selectedNode ? (
          <AreasContainer>
            <AreaConfig node={selectedNode} updateUI={updateUI} />
          </AreasContainer>
        ) : (
          selectedLink && (
            <AreasContainer>
              <AreaConfig updateUI={updateUI} />
            </AreasContainer>
          )
        )
      }
      secondaryContent={
        filteredNodes &&
        !selectedLink &&
        !selectedNode && (
          <ListElement
            currentElement={currentNode.toUpperCase()} // TODO replace
            setSelectedItem={(node) => {
              dispatch(setSelectedNode(node));
            }}
            list={filteredNodes}
          />
        )
      }
      onSearchFilterChange={(searchedNodes) => {
        setSearchValue(searchedNodes);
      }}
      onAdd={!selectedNode ? onAdd : undefined}
    />
  );
}

export default Areas;
