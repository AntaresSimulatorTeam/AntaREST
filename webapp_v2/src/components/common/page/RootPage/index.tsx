import { SvgIconComponent } from "@mui/icons-material";
import { ElementType, PropsWithChildren, ReactNode } from "react";
import BasicPage from "../BasicPage";
import {
  HeaderBottom,
  HeaderTop,
  HeaderTopRight,
  Title,
  TitleWrapper,
} from "./styles";

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
          <HeaderTop>
            <TitleWrapper>
              {TitleIcon && (
                <TitleIcon
                  sx={{
                    color: "text.secondary",
                    width: "42px",
                    height: "42px",
                  }}
                />
              )}
              <Title>{title}</Title>
            </TitleWrapper>
            {headerTopRight && (
              <HeaderTopRight>{headerTopRight}</HeaderTopRight>
            )}
          </HeaderTop>
          {headerBottom && <HeaderBottom>{headerBottom}</HeaderBottom>}
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
