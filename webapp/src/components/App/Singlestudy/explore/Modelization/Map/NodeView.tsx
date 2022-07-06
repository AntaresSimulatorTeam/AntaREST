import { useEffect, useRef } from "react";
import { Box, styled } from "@mui/material";
import AddLinkIcon from "@mui/icons-material/AddLink";
import { NodeProperties } from "../../../../../../common/types";
import { rgbToHsl } from "../../../../../../services/utils";

const nodeStyle = {
  opacity: ".9",
  minWidth: "40px",
  textAlign: "center",
  padding: "4px",
  borderRadius: "30px",
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
  height: "20px",
  backgroundColor: "#555",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  fontSize: "16px",
};

const StyledLink = styled(AddLinkIcon)(({ theme }) => ({
  marginLeft: theme.spacing(1),
  color: theme.palette.secondary.main,
  "&:hover": {
    color: theme.palette.secondary.dark,
  },
}));

interface PropType {
  node: NodeProperties;
  linkCreation: (id: string) => void;
}

function NodeView(props: PropType) {
  const nodeRef = useRef<HTMLDivElement>(null);
  const { node, linkCreation } = props;

  const hslColors = rgbToHsl(node.color || "rgb(211, 211, 211)");

  useEffect(() => {
    if (nodeRef.current) {
      const parentNodeClickedWidth =
        nodeRef.current.parentElement?.parentElement?.parentElement?.getAttribute(
          "width"
        );
      const parentNodePrevWidth =
        nodeRef.current.parentElement?.parentElement?.parentElement?.getAttribute(
          "prevWidth"
        );
      if (node.highlighted) {
        if (
          parentNodeClickedWidth !== null &&
          parentNodeClickedWidth &&
          !parentNodePrevWidth
        ) {
          const newSizeClickedWidth = parseInt(parentNodeClickedWidth, 10) + 32;
          nodeRef.current.parentElement?.parentElement?.parentElement?.setAttribute(
            "width",
            `${newSizeClickedWidth}`
          );
          nodeRef.current.parentElement?.parentElement?.parentElement?.setAttribute(
            "prevWidth",
            parentNodeClickedWidth
          );
          nodeRef.current.parentElement?.style.setProperty(
            "width",
            `${newSizeClickedWidth}px`
          );
        }
      } else if (parentNodePrevWidth) {
        const newSize = parseInt(parentNodePrevWidth, 10);
        nodeRef.current.parentElement?.parentElement?.parentElement?.setAttribute(
          "width",
          `${newSize}`
        );
        nodeRef.current.parentElement?.style.setProperty(
          "width",
          `${newSize}px`
        );
        nodeRef.current.parentElement?.parentElement?.parentElement?.removeAttribute(
          "prevWidth"
        );
      }
    }
  }, [node]);

  return (
    <Box
      ref={nodeRef}
      width="100%"
      height="100%"
      display="flex"
      padding="4px"
      marginTop="2px"
      marginLeft="2px"
    >
      {node.highlighted ? (
        <>
          <Box
            sx={{
              ...nodeStyle,
              opacity: 1,
              bgcolor: `hsl(${hslColors[0]}, ${hslColors[1]}%, ${hslColors[2]}%)`,
              color:
                hslColors[2] >= 75 ||
                (hslColors[0] >= 50 && hslColors[0] <= 75 && hslColors[2] >= 50)
                  ? "black"
                  : "white",
              boxShadow: `0px 0px 4px 2px hsl(${hslColors[0]}, ${hslColors[1]}%, ${hslColors[2]}%)`,
            }}
          >
            {node.name}
          </Box>
          <StyledLink
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              linkCreation(node.id);
            }}
          />
        </>
      ) : (
        <Box
          sx={{
            ...nodeStyle,
            bgcolor: `hsl(${hslColors[0]}, ${hslColors[1]}%, ${hslColors[2]}%)`,
            color:
              hslColors[2] >= 75 ||
              (hslColors[0] >= 50 && hslColors[0] <= 75 && hslColors[2] >= 50)
                ? "black"
                : "white",
          }}
        >
          {node.name}
        </Box>
      )}
    </Box>
  );
}

export default NodeView;
