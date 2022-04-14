import { Divider } from "@mui/material";
import { PropsWithChildren, ReactNode } from "react";
import { Header, Root } from "./styles";

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
    <Root>
      {header && (
        <Header>
          {header}
          {hideHeaderDivider ? null : <Divider />}
        </Header>
      )}
      {children}
    </Root>
  );
}

BasicPage.defaultProps = {
  header: null,
  hideHeaderDivider: false,
};

export default BasicPage;
