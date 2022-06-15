import { Box, ListItemButton, ListItemIcon, ListItemText } from "@mui/material";
import ArrowRightOutlinedIcon from "@mui/icons-material/ArrowRightOutlined";

interface PropsType<T> {
  list: Array<T>;
  currentElement?: string;
  setSelectedItem: (item: T, index: number) => void;
}

function ListElement<T extends { name: string }>(props: PropsType<T>) {
  const { list, currentElement, setSelectedItem } = props;

  return (
    <Box
      width="100%"
      flexGrow={1}
      flexShrink={1}
      sx={{ pl: 2, pt: 1, pr: 1, mb: 1, overflow: "auto" }}
    >
      {list.map((element, index) => (
        <ListItemButton
          selected={currentElement === element.name}
          onClick={() => setSelectedItem(element, index)}
          key={element.name}
          sx={{
            width: "100%",
            display: "flex",
            justifyContent: "space-between",
          }}
        >
          <ListItemText
            sx={{ "&> span": { textOverflow: "ellipsis", overflow: "hidden" } }}
          >
            {element.name}
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
        </ListItemButton>
      ))}
    </Box>
  );
}

ListElement.defaultProps = {
  currentElement: undefined,
};

export default ListElement;
