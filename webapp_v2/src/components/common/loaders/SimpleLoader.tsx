import { useTranslation } from "react-i18next";
import { Box, CircularProgress } from "@mui/material";

interface PropTypes {
  progress?: number;
  message?: string;
  color?: string;
}

function SimpleLoader(props: PropTypes) {
  const [t] = useTranslation();
  const { progress, message, color } = props;
  return (
    <>
      <Box
        display="flex"
        alignItems="center"
        justifyContent="center"
        position="absolute"
        width="100%"
        height="100%"
        zIndex={999}
      >
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
        >
          {progress === undefined ? (
            <CircularProgress sx={{ width: "98px", height: "98px" }} />
          ) : (
            <CircularProgress
              variant="determinate"
              sx={{ width: "98px", height: "98px" }}
              value={progress}
            />
          )}
          {message && <Box mt={t}>{t(message)}</Box>}
        </Box>
      </Box>
      <Box
        display="flex"
        alignItems="center"
        justifyContent="center"
        position="absolute"
        width="100%"
        height="100%"
        zIndex={998}
        sx={{ opacity: 0.9, bgcolor: color }}
      />
    </>
  );
}

SimpleLoader.defaultProps = {
  progress: undefined,
  message: undefined,
  color: "rgba(0,0,0,0)",
};

export default SimpleLoader;
