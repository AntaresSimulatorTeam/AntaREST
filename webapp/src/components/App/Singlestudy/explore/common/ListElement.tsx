import {
  Box,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  PopoverPosition,
  SxProps,
  Theme,
} from "@mui/material";
import ArrowRightOutlinedIcon from "@mui/icons-material/ArrowRightOutlined";
import { useState } from "react";
import { IdType } from "../../../../../common/types";
import { mergeSxProp } from "../../../../../utils/muiUtils";

interface Props<T> {
  list: T[];
  currentElement?: string;
  currentElementKeyToTest?: keyof T;
  setSelectedItem: (item: T, index: number) => void;
  contextMenuContent?: (props: {
    element: T;
    close: VoidFunction;
  }) => React.ReactElement;
  sx?: SxProps<Theme>;
}

function ListElement<T extends { id?: IdType; name: string; label?: string }>({
  list,
  currentElement,
  currentElementKeyToTest,
  setSelectedItem,
  contextMenuContent: ContextMenuContent,
  sx,
}: Props<T>) {
  const [contextMenuPosition, setContextMenuPosition] =
    useState<PopoverPosition | null>(null);
  const [elementForContext, setElementForContext] = useState<T>();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleContextMenu = (element: T) => (event: React.MouseEvent) => {
    event.preventDefault();

    if (!ContextMenuContent) {
      return;
    }

    setElementForContext(element);

    setContextMenuPosition(
      contextMenuPosition === null
        ? {
            left: event.clientX + 2,
            top: event.clientY - 6,
          }
        : // Repeated context menu when it is already open closes it with Chrome 84 on Ubuntu
          // Other native context menus might behave different.
          // With this behavior we prevent contextmenu from the backdrop to re-locale existing context menus.
          null,
    );
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      width="100%"
      flexGrow={1}
      flexShrink={1}
      sx={mergeSxProp({ overflow: "auto", py: 1 }, sx)}
    >
      {list.map((element, index) => (
        <ListItemButton
          selected={
            currentElement === element[currentElementKeyToTest || "name"]
          }
          onClick={() => setSelectedItem(element, index)}
          key={element.id || element.name}
          sx={{
            width: "100%",
            display: "flex",
            justifyContent: "space-between",
            py: 0,
          }}
          onContextMenu={handleContextMenu(element)}
        >
          <ListItemText
            sx={{
              "&> span": { textOverflow: "ellipsis", overflow: "hidden" },
            }}
          >
            {element.label || element.name}
          </ListItemText>
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
          {ContextMenuContent && elementForContext && (
            <Menu
              open={contextMenuPosition !== null}
              onClose={() => setContextMenuPosition(null)}
              anchorReference="anchorPosition"
              anchorPosition={
                contextMenuPosition !== null ? contextMenuPosition : undefined
              }
            >
              <ContextMenuContent
                element={elementForContext}
                close={() => setContextMenuPosition(null)}
              />
            </Menu>
          )}
        </ListItemButton>
      ))}
    </Box>
  );
}

export default ListElement;
