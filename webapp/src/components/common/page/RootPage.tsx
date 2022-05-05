import { SvgIconComponent } from "@mui/icons-material";
import { Box, Typography } from "@mui/material";
import { ElementType, PropsWithChildren, ReactNode } from "react";
import BasicPage from "./BasicPage";

/**
 * Types
 */

interface Props {
  title: string;
  titleIcon?: ElementType<SvgIconComponent>;
  headerTopRight?: ReactNode;
  headerBottom?: ReactNode;
  hideHeaderDivider?: boolean;
}

/**
 * Component
 */

function RootPage(props: PropsWithChildren<Props>) {
  const {
    title,
    titleIcon,
    headerTopRight,
    headerBottom,
    children,
    hideHeaderDivider,
  } = props;

  const TitleIcon = titleIcon as SvgIconComponent;

  return (
    <BasicPage
      header={
        <>
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              mb: 1,
            }}
          >
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                flex: 1,
              }}
            >
              {TitleIcon && (
                <TitleIcon
                  sx={{
                    color: "text.secondary",
                    width: "42px",
                    height: "42px",
                  }}
                />
              )}
              <Typography sx={{ ml: 2, fontSize: 34 }}>{title}</Typography>
            </Box>
            {headerTopRight && (
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "flex-end",
                  flex: 1,
                }}
              >
                {headerTopRight}
              </Box>
            )}
          </Box>
          {headerBottom && <Box sx={{ width: 1, mb: 1 }}>{headerBottom}</Box>}
        </>
      }
      hideHeaderDivider={hideHeaderDivider}
    >
      {children}
    </BasicPage>
  );
}

RootPage.defaultProps = {
  titleIcon: null,
  headerTopRight: null,
  headerBottom: null,
  hideHeaderDivider: false,
};

export default RootPage;
