/* eslint-disable jsx-a11y/no-static-element-interactions */
import { memo } from "react";
import { Typography, Box, styled } from "@mui/material";
import AutoSizer from "react-virtualized-auto-sizer";
import { FixedSizeList, areEqual, ListChildComponentProps } from "react-window";
import ArrowRightIcon from "@mui/icons-material/ArrowRight";
import {
  XpansionCandidate,
  XpansionRenderView,
} from "../../../../common/types";
import { scrollbarStyle } from "../../../../theme";

const ROW_ITEM_SIZE = 45;
const BUTTONS_SIZE = 40;

const StyledList = styled(FixedSizeList)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  "&> div > div": {
    cursor: "pointer",
    "&:hover": {
      textDecoration: "underline",
      color: theme.palette.primary.main,
      "&>svg": {
        color: `${theme.palette.primary.main} !important`,
      },
    },
  },
  ...scrollbarStyle,
}));

interface PropsType {
  candidates: Array<XpansionCandidate> | undefined;
  selectedItem: string;
  setSelectedItem: (item: string) => void;
  setView: (item: XpansionRenderView | undefined) => void;
}

const Row = memo((props: ListChildComponentProps) => {
  const { data, index, style } = props;
  const { candidates, setSelectedItem, selectedItem, setView } = data;
  const candidate = candidates[index];

  return (
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events
    <Box
      sx={
        selectedItem && selectedItem.name === candidate.name
          ? {
              display: "flex",
              justifyContent: "space-evenly",
              alignItems: "center",
              ...style,
              textDecoration: "underline",
            }
          : {
              display: "flex",
              justifyContent: "space-evenly",
              alignItems: "center",
              ...style,
            }
      }
      onClick={() => {
        setSelectedItem(candidate.name);
        setView(XpansionRenderView.candidate);
      }}
    >
      <Typography
        sx={{
          display: "block",
          width: "200px",
          textOverflow: "ellipsis",
          overflow: "hidden",
        }}
      >
        {candidate.name}
      </Typography>
      <ArrowRightIcon
        sx={
          selectedItem && selectedItem.name === candidate.name
            ? { color: "primary.main" }
            : { color: "action.active" }
        }
      />
    </Box>
  );
}, areEqual);

function CandidateListing(props: PropsType) {
  const { candidates = [], selectedItem, setSelectedItem, setView } = props;

  return (
    <Box
      sx={{
        width: "100%",
        minHeight: "100px",
        color: "text.secondary",
        display: "flex",
        flexGrow: 1,
        flexShrink: 1,
        marginBottom: "120px",
      }}
    >
      {candidates && candidates.length > 0 && (
        <AutoSizer>
          {({ height, width }) => {
            const idealHeight = ROW_ITEM_SIZE * candidates.length;
            return (
              <StyledList
                height={
                  idealHeight > height
                    ? height + ROW_ITEM_SIZE - BUTTONS_SIZE
                    : idealHeight
                }
                width={width}
                itemCount={candidates.length}
                itemSize={ROW_ITEM_SIZE}
                itemData={{
                  candidates,
                  setSelectedItem,
                  selectedItem,
                  setView,
                }}
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

export default CandidateListing;
