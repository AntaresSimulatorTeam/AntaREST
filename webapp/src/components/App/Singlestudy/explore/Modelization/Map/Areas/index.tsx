import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { StudyMetadata, UpdateAreaUi } from "../../../../../../../common/types";
import PropertiesView from "../../../../../../common/PropertiesView";
import ListElement from "../../../common/ListElement";
import { AreasContainer } from "../style";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import {
  getCurrentLink,
  getCurrentStudyMapNode,
} from "../../../../../../../redux/selectors";
import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";
import AreaConfig from "./AreaConfig";
import { isSearchMatching } from "../../../../../../../utils/textUtils";
import { setCurrentArea } from "../../../../../../../redux/ducks/studySyntheses";
import { AreaNode } from "../../../../../../../redux/ducks/studyMaps";

interface Props {
  onAdd: () => void;
  updateUI: (id: string, value: UpdateAreaUi) => void;
  nodes: AreaNode[];
}

function Areas(props: Props) {
  const { onAdd, updateUI, nodes } = props;
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();
  const [filteredNodes, setFilteredNodes] = useState<Array<AreaNode>>([]);
  const [searchValue, setSearchValue] = useState("");
  const currentLink = useAppSelector((state) =>
    getCurrentLink(state, study.id)
  );
  const currentArea = useAppSelector(getCurrentStudyMapNode);

  useEffect(() => {
    const filter = (): AreaNode[] => {
      if (nodes) {
        return nodes.filter((node) => isSearchMatching(searchValue, node.id));
      }
      return [];
    };

    setFilteredNodes(filter());
  }, [nodes, searchValue]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <PropertiesView
      mainContent={
        currentArea ? (
          <AreasContainer>
            <AreaConfig currentArea={currentArea} updateUI={updateUI} />
          </AreasContainer>
        ) : (
          currentLink && (
            <AreasContainer>
              <AreaConfig updateUI={updateUI} currentLink={currentLink} />
            </AreasContainer>
          )
        )
      }
      secondaryContent={
        filteredNodes &&
        !currentLink &&
        !currentArea && (
          <ListElement
            setSelectedItem={(node) => {
              dispatch(setCurrentArea(node.id));
            }}
            list={filteredNodes}
          />
        )
      }
      onSearchFilterChange={(searchValue) => {
        setSearchValue(searchValue);
      }}
      onAdd={!currentArea ? onAdd : undefined}
    />
  );
}

export default Areas;
