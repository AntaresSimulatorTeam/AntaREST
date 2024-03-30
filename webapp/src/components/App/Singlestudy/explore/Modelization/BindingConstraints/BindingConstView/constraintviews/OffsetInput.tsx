import HighlightOffIcon from "@mui/icons-material/HighlightOff";
import { Box } from "@mui/material";
import { PropsWithChildren } from "react";

interface Props {
  onRemove: () => void;
}

export default function OffsetInput(props: PropsWithChildren<Props>) {
  const { onRemove, children } = props;
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        position: "relative",
      }}
    >
      <HighlightOffIcon
        sx={{
          position: "absolute",
          top: "-15px",
          right: "-25px",
          color: "error.main",
          cursor: "pointer",
          "&:hover": {
            color: "error.light",
          },
        }}
        onClick={onRemove}
      />
      {children}
    </Box>
  );
}
