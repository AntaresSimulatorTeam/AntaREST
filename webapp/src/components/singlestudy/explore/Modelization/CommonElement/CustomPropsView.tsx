import {
  Box,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from "@mui/material";
import ArrowRightOutlinedIcon from "@mui/icons-material/ArrowRightOutlined";
import { useCallback, useEffect, useState } from "react";
import PropertiesView from "../../../../common/PropertiesView";

interface PropsType<T> {
  element: Array<T> | undefined;
  onClick: (name: string) => void;
  currentElement: string | undefined;
}
function CustomPropsView<T extends { name: string }>(props: PropsType<T>) {
  const { element, onClick, currentElement } = props;
  const [nameFilter, setNameFilter] = useState<string>();
  const [filteredData, setFilteredData] = useState<Array<T>>(element || []);

  const filter = useCallback(
    (currentName?: string): Array<T> => {
      if (element) {
        return element.filter(
          (s) =>
            !currentName || s.name.search(new RegExp(currentName, "i")) !== -1
        );
      }
      return [];
    },
    [element]
  );

  useEffect(() => {
    setFilteredData(filter(nameFilter));
  }, [filter, element, nameFilter]);
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
            {filteredData?.map((elm) => (
              <ListItemButton
                selected={currentElement === elm.name}
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
      onSearchFilterChange={(e) => setNameFilter(e as string)}
    />
  );
}

export default CustomPropsView;
