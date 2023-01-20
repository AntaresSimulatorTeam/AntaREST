import { Help } from "@mui/icons-material";
import { Tooltip, IconButton, Box, SxProps, Theme } from "@mui/material";
import { mergeSxProp } from "../../utils/muiUtils";

interface Props {
  to: string;
  isAbsolute?: boolean;
  sx?: SxProps<Theme>;
}

function DocLink({ to, isAbsolute, sx }: Props) {
  const DOC_LINK = `https://antares-simulator.readthedocs.io/en/latest/reference-guide/04-active_windows/#${to}`;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={mergeSxProp(
        isAbsolute
          ? {
              position: "absolute",
              right: "20px",
              top: "5px",
            }
          : sx
      )}
    >
      <Tooltip title="View documentation">
        <IconButton
          href={DOC_LINK}
          target="_blank"
          rel="noopener noreferrer"
          color="default"
        >
          <Help />
        </IconButton>
      </Tooltip>
    </Box>
  );
}

export default DocLink;
