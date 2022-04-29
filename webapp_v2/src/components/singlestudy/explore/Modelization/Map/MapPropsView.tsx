import { useCallback, useEffect, useState } from "react";
import { Box } from "@mui/material";
import {
  LinkProperties,
  NodeProperties,
  UpdateAreaUi,
  isNode,
} from "../../../../../common/types";
import PanelView from "./PanelView";
import NodeListing from "./NodeListing";
import PropertiesView from "../../../../common/PropertiesView";

interface PropsType {
  item?: NodeProperties | LinkProperties | undefined;
  setSelectedItem: (item: NodeProperties | LinkProperties | undefined) => void;
  nodeList: Array<NodeProperties>;
  nodeLinks?: Array<LinkProperties> | undefined;
  onDelete?: (id: string, target?: string) => void;
  onArea: () => void;
  updateUI: (id: string, value: UpdateAreaUi) => void;
}

function MapPropsView(props: PropsType) {
  const {
    item,
    setSelectedItem,
    nodeList,
    nodeLinks,
    onDelete,
    onArea,
    updateUI,
  } = props;
  const [filteredNodes, setFilteredNodes] =
    useState<Array<NodeProperties>>(nodeList);
  const [nodeNameFilter, setNodeNameFilter] = useState<string>();

  const filter = useCallback(
    (currentName?: string): NodeProperties[] => {
      if (nodeList) {
        return nodeList.filter(
          (s) =>
            !currentName || s.id.search(new RegExp(currentName, "i")) !== -1
        );
      }
      return [];
    },
    [nodeList]
  );

  useEffect(() => {
    setFilteredNodes(filter(nodeNameFilter));
  }, [filter, nodeList, nodeNameFilter]);

  return (
    <PropertiesView
      mainContent={
        item && isNode(item) && onDelete ? (
          <Box
            width="100%"
            flexGrow={1}
            flexShrink={1}
            display="flex"
            flexDirection="column"
            justifyContent="flex-start"
            alignItems="center"
          >
            <PanelView
              node={item as NodeProperties}
              links={nodeLinks}
              onDelete={onDelete}
              updateUI={updateUI}
              setSelectedItem={setSelectedItem}
            />
          </Box>
        ) : (
          item &&
          onDelete && (
            <Box
              width="100%"
              flexGrow={1}
              flexShrink={1}
              display="flex"
              flexDirection="column"
              justifyContent="flex-start"
              alignItems="center"
            >
              <PanelView
                link={item as LinkProperties}
                nodes={nodeList}
                onDelete={onDelete}
                updateUI={updateUI}
                setSelectedItem={setSelectedItem}
              />
            </Box>
          )
        )
      }
      secondaryContent={
        filteredNodes &&
        !item && (
          <NodeListing
            nodes={filteredNodes}
            setSelectedItem={setSelectedItem}
          />
        )
      }
      onSearchFilterChange={(e) => setNodeNameFilter(e as string)}
      onAdd={!item ? onArea : undefined}
    />
  );
}

MapPropsView.defaultProps = {
  item: undefined,
  nodeLinks: undefined,
  onDelete: undefined,
};

export default MapPropsView;
