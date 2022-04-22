import { Box, Divider } from "@mui/material";
import { PropsWithChildren, ReactNode } from "react";

/**
 * Types
 */

interface Props {
  header?: ReactNode;
  hideHeaderDivider?: boolean;
}

/**
 * Component
 */

function BasicPage(props: PropsWithChildren<Props>) {
  const { header, hideHeaderDivider, children } = props;

  return (
    <Box sx={{ height: 1, display: "flex", flexDirection: "column" }}>
      {header && (
        <Box sx={{ width: 1, py: 2, px: 3 }}>
          {header}
          {hideHeaderDivider ? null : <Divider />}
        </Box>
      )}
      {children}
    </Box>
  );
}

BasicPage.defaultProps = {
  header: null,
  hideHeaderDivider: false,
};

export default BasicPage;
