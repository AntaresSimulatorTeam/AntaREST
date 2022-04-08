import { Box, Divider, styled } from "@mui/material";
import { PropsWithChildren, ReactNode } from "react";

/**
 * Styles
 */

const Header = styled("div")(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "center",
  padding: theme.spacing(2, 0),
  boxSizing: "border-box",
}));

/**
 * Types
 */

type PropTypes = {
  header?: ReactNode;
};

/**
 * Component
 */

function BasicPage(props: PropsWithChildren<PropTypes>) {
  const { header, children } = props;

  return (
    <Box
      width="100%"
      height="100%"
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      alignItems="center"
      boxSizing="border-box"
      overflow="hidden"
    >
      {header && <Header>{header}</Header>}
      <Divider sx={{ width: "98%" }} />
      {children}
    </Box>
  );
}

BasicPage.defaultProps = {
  header: null,
};

export default BasicPage;
