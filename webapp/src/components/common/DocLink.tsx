import { Help } from "@mui/icons-material";
import { Tooltip, IconButton, SxProps, Theme } from "@mui/material";

interface Props {
  to: string;
  sx?: SxProps<Theme>;
}

function DocLink({ to, sx }: Props) {
  return (
    <Tooltip title="View documentation" sx={sx}>
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
