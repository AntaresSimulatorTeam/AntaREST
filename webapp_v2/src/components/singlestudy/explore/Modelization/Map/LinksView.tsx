import { memo } from "react";
import { ListItemText, ListItem, Typography, Box, styled } from "@mui/material";
import { useTranslation } from "react-i18next";
import AutoSizer from "react-virtualized-auto-sizer";
import { areEqual, FixedSizeList, ListChildComponentProps } from "react-window";
import { LinkProperties, NodeProperties } from "../../../../../common/types";
import { scrollbarStyle } from "../../../../../theme";

const ROW_ITEM_SIZE = 40;
const BUTTONS_SIZE = 40;

const StyledList = styled(FixedSizeList)(({ theme }) => ({
  "&> div > li > div": {
    cursor: "pointer",
    "&:hover": {
      textDecoration: "underline",
    },
  },
  ...scrollbarStyle,
}));

interface PropsType {
  links: Array<LinkProperties>;
  node: NodeProperties;
  setSelectedItem: (item: NodeProperties | LinkProperties | undefined) => void;
}

const Row = memo((props: ListChildComponentProps) => {
  const { data, index, style } = props;
  const { links, node, setSelectedItem } = data;
  const link =
    links[index].source === node.id ? links[index].target : links[index].source;
  const linkData =
    links[index].source === node.id
      ? { source: links[index].source, target: links[index].target }
      : { source: links[index].target, target: links[index].source };

  return (
    <ListItem key={index} style={style}>
      <ListItemText
        primary={link}
        onClick={() => setSelectedItem(linkData)}
        sx={{
          width: "100%",
          color: "text.secondary",
          "&:hover": { textDecoration: "underline", color: "text.primary" },
        }}
      />
    </ListItem>
  );
}, areEqual);

function LinksView(props: PropsType) {
  const { links, node, setSelectedItem } = props;
  const [t] = useTranslation();

  return (
    <Box
      width="100%"
      flexGrow={1}
      flexShrink={1}
      minHeight="100px"
      padding="8px"
      marginTop="4px"
    >
      {links.length >= 1 && (
        <Typography
          sx={{
            width: "90%",
            mb: 1,
            color: "text.secondary",
            boxSizing: "border-box",
            fontWeight: "bold",
          }}
        >
          {t("singlestudy:links")}
        </Typography>
      )}
      <AutoSizer>
        {({ height, width }) => {
          const idealHeight = ROW_ITEM_SIZE * links.length;
          return (
            <StyledList
              height={
                idealHeight > height - BUTTONS_SIZE
                  ? height - BUTTONS_SIZE
                  : idealHeight
              }
              width={width}
              itemSize={ROW_ITEM_SIZE}
              itemCount={links.length}
              itemData={{ links, node, setSelectedItem }}
            >
              {Row}
            </StyledList>
          );
        }}
      </AutoSizer>
    </Box>
  );
}

export default LinksView;
