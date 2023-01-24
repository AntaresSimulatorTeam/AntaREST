import { Help } from "@mui/icons-material";
import { Tooltip, IconButton, SxProps, Theme } from "@mui/material";
import { mergeSxProp } from "../../utils/muiUtils";

interface Props {
  to: string;
  isAbsolute?: boolean;
  sx?: SxProps<Theme>;
}

function DocLink({ to, isAbsolute, sx }: Props) {
  return (
    <Tooltip
      title="View documentation"
      sx={mergeSxProp(
        isAbsolute
          ? {
              position: "absolute",
              right: "20px",
              top: "5px",
            }
          : {},
        sx
      )}
    >
      <IconButton
        href={to}
        target="_blank"
        rel="noopener noreferrer"
        color="default"
      >
        <Help />
      </IconButton>
    </Tooltip>
  );
}

export default DocLink;
