import {
  Box,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from "@mui/material";
import ArrowRightOutlinedIcon from "@mui/icons-material/ArrowRightOutlined";
import { useCallback, useEffect, useState } from "react";
import { Area } from "../../../../../common/types";
import PropertiesView from "../../../../common/PropertiesView";

interface PropsType {
  areas: Array<Area> | undefined;
  onClick: (name: string) => void;
  currentArea: string | undefined;
}
function AreaPropsView(props: PropsType) {
  const { areas, onClick, currentArea } = props;
  console.log("MY AREAS: ", areas);

  const [areaNameFilter, setAreaNameFilter] = useState<string>();
  const [filteredAreas, setFilteredAreas] = useState<Array<Area>>(areas || []);

  const filter = useCallback(
    (currentName?: string): Array<Area> => {
      if (areas) {
        return areas.filter(
          (s) =>
            !currentName || s.name.search(new RegExp(currentName, "i")) !== -1
        );
      }
      return [];
    },
    [areas]
  );

  useEffect(() => {
    setFilteredAreas(filter(areaNameFilter));
  }, [filter, areas, areaNameFilter]);
  return (
    <PropertiesView
      mainContent={
        <Box
          width="100%"
          flexGrow={1}
          flexShrink={1}
          display="flex"
          flexDirection="column"
          justifyContent="flex-start"
          alignItems="center"
          overflow="auto"
        >
          <List sx={{ width: "95%" }}>
            {filteredAreas?.map((elm) => (
              <ListItemButton
                selected={currentArea === elm.name}
                onClick={() => onClick(elm.name)}
                key={elm.name}
                sx={{
                  width: "100%",
                  display: "flex",
                  justifyContent: "space-between",
                }}
              >
                <ListItemText>{elm.name}</ListItemText>
                <ListItemIcon
                  sx={{
                    minWidth: 0,
                    width: "auto",
                    p: 0,
                    display: "flex",
                  }}
                >
                  <ArrowRightOutlinedIcon color="primary" />
                </ListItemIcon>
              </ListItemButton>
            ))}
          </List>
        </Box>
      }
      secondaryContent={<div />}
      onSearchFilterChange={(e) => setAreaNameFilter(e as string)}
      onAdd={() => console.log("ADD")}
    />
  );
}

export default AreaPropsView;
