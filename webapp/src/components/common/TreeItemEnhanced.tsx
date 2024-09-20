import { TreeItem, type TreeItemProps } from "@mui/x-tree-view/TreeItem";
import { mergeSxProp } from "../../utils/muiUtils";
import * as RA from "ramda-adjunct";

export type TreeItemEnhancedProps = TreeItemProps;

function TreeItemEnhanced({ onClick, sx, ...rest }: TreeItemEnhancedProps) {
  const canExpand = rest.children && RA.isNotEmpty(rest.children);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleClick: TreeItemEnhancedProps["onClick"] = (event) => {
    const { target } = event;

    // The item is not selected if the click is on the expand/collapse icon
    if (
      canExpand &&
      target instanceof Element &&
      target.closest(".MuiTreeItem-iconContainer")
    ) {
      return;
    }

    onClick?.(event);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TreeItem
      {...rest}
      onClick={handleClick}
      sx={mergeSxProp(
        {
          "& > .MuiTreeItem-content": {
            p: 0,
            alignItems: "normal",
            // Expand/collapse icon
            "& > .MuiTreeItem-iconContainer": {
              alignItems: "center",
              borderTopLeftRadius: "inherit",
              borderBottomLeftRadius: "inherit",
              "&:hover": {
                background: canExpand ? "inherit" : "none",
              },
            },
            "& > .MuiTreeItem-label": {
              py: 0.5,
            },
          },
        },
        sx,
      )}
    />
  );
}

export default TreeItemEnhanced;
