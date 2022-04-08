import { Box, Typography } from "@mui/material";
import { ElementType, PropsWithChildren, ReactNode } from "react";
import BasicPage from "./BasicPage";

/**
 * Types
 */

type PropTypes = {
  title: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  titleIcon?: ElementType<any>; // TODO: replace any
  headerRight?: ReactNode;
  headerBottom?: ReactNode;
};

/**
 * Component
 */

function RootPage(props: PropsWithChildren<PropTypes>) {
  const {
    title,
    titleIcon: TitleIcon,
    headerRight,
    headerBottom,
    children,
  } = props;

  return (
    <BasicPage
      header={
        <>
          <Box width="100%" alignItems="center" display="flex">
            <Box alignItems="center" display="flex">
              {TitleIcon && (
                <TitleIcon
                  sx={{
                    color: "text.secondary",
                    width: "42px",
                    height: "42px",
                  }}
                />
              )}
              <Typography color="white" sx={{ ml: 2, fontSize: "34px" }}>
                {title}
              </Typography>
            </Box>
            {headerRight && (
              <Box
                alignItems="center"
                justifyContent="flex-end"
                flexGrow={1}
                display="flex"
              >
                {headerRight}
              </Box>
            )}
          </Box>
          {headerBottom && (
            <Box display="flex" width="100%" alignItems="center">
              {headerBottom}
            </Box>
          )}
        </>
      }
    >
      {children}
    </BasicPage>
  );
}

RootPage.defaultProps = {
  titleIcon: null,
  headerRight: null,
  headerBottom: null,
};

export default RootPage;
