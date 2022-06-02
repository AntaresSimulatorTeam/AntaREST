/* eslint-disable jsx-a11y/no-static-element-interactions */
import { memo } from "react";
import {
  Box,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  styled,
} from "@mui/material";
import ArrowRightOutlinedIcon from "@mui/icons-material/ArrowRightOutlined";
import AutoSizer from "react-virtualized-auto-sizer";
import { FixedSizeList, areEqual, ListChildComponentProps } from "react-window";
import { scrollbarStyle } from "../../../../theme";

const ROW_ITEM_SIZE = 30;

const StyledList = styled(FixedSizeList)(({ theme }) => ({
  "&> div > div": {
    color: theme.palette.text.secondary,
    cursor: "pointer",
    "&:hover": {
      color: theme.palette.text.primary,
    },
  },
  ...scrollbarStyle,
}));

interface PropsType<T> {
  list: Array<T>;
  currentElement?: string;
  setSelectedItem: (item: T) => void;
}

const Row = memo((props: ListChildComponentProps) => {
  const { data, index, style } = props;
  const { list, currentElement, setSelectedItem } = data;
  const element = list[index];
  return (
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events
    <ListItemButton
      selected={currentElement === element.name}
      onClick={() => setSelectedItem(element)}
      key={element.name}
      sx={{
        width: "100%",
        display: "flex",
        justifyContent: "space-between",
        ...style,
      }}
    >
      <ListItemText>{element.name}</ListItemText>
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
  );
}, areEqual);

function ListElement<T extends { name: string }>(props: PropsType<T>) {
  const { list, currentElement, setSelectedItem } = props;

  return (
    <Box
      width="100%"
      flexGrow={1}
      flexShrink={1}
      sx={{ pl: 2, pt: 1, pr: 1, mb: 1 }}
    >
      {list.length > 0 && list && (
        <AutoSizer>
          {({ height, width }) => {
            const idealHeight = ROW_ITEM_SIZE * list.length;
            return (
              <StyledList
                height={idealHeight > height ? height : idealHeight}
                width={width}
                itemCount={list.length}
                itemSize={ROW_ITEM_SIZE}
                itemData={{ list, currentElement, setSelectedItem }}
              >
                {Row}
              </StyledList>
            );
          }}
        </AutoSizer>
      )}
    </Box>
  );
}

ListElement.defaultProps = {
  currentElement: undefined,
};

export default ListElement;
