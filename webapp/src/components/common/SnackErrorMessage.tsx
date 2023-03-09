import { useState, forwardRef, useCallback } from "react";
import * as React from "react";
import { useSnackbar, SnackbarContent } from "notistack";
import axios from "axios";
import {
  Box,
  Card,
  CardActions,
  Collapse,
  Grid,
  IconButton,
  Paper,
  styled,
  Typography,
} from "@mui/material";
import CancelRoundedIcon from "@mui/icons-material/CancelRounded";
import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

const Snackbar = styled(SnackbarContent)(({ theme }) => ({
  [theme.breakpoints.up("sm")]: {
    minWidth: "344px !important",
  },
}));

const Label = styled(Typography)(({ theme }) => ({
  fontWeight: "bold",
  marginRight: theme.spacing(1),
}));

export const ExpandButton = styled(IconButton, {
  shouldForwardProp: (prop) => prop !== "expanded",
})<{ expanded?: boolean }>(({ theme, expanded }) => ({
  padding: "8px 8px",
  transform: expanded === true ? "rotate(180deg)" : "rotate(0deg)",
  color: "white",
  transition: theme.transitions.create("transform", {
    duration: theme.transitions.duration.shortest,
  }),
}));

interface Props {
  id: string | number;
  message: string | React.ReactNode;
  details: string | Error;
}

const SnackErrorMessage = forwardRef<HTMLDivElement, Props>(
  (props: Props, ref) => {
    const { closeSnackbar } = useSnackbar();
    const [expanded, setExpanded] = useState(false);
    const { id, message, details } = props;

    const handleExpandClick = useCallback(() => {
      setExpanded((oldExpanded) => !oldExpanded);
    }, []);

    const handleDismiss = useCallback(() => {
      closeSnackbar(id);
    }, [id, closeSnackbar]);

    return (
      <Snackbar ref={ref}>
        <Card
          sx={{
            bgcolor: "error.main",
            width: "100%",
            color: "white",
          }}
        >
          <CardActions
            sx={{
              root: {
                padding: "8px 8px 8px 16px",
                justifyContent: "space-between",
                alignItems: "center",
              },
            }}
          >
            <CancelRoundedIcon sx={{ width: "20px", height: "20px", mx: 1 }} />
            <Typography variant="subtitle2">{message}</Typography>
            <Box ml="auto">
              <ExpandButton
                aria-label="Show more"
                expanded={expanded}
                onClick={handleExpandClick}
              >
                <ExpandMoreIcon />
              </ExpandButton>
              <ExpandButton onClick={handleDismiss}>
                <CloseRoundedIcon />
              </ExpandButton>
            </Box>
          </CardActions>
          <Collapse in={expanded} timeout="auto" unmountOnExit>
            <Paper sx={{ p: 2 }}>
              {axios.isAxiosError(details) ? (
                <Grid
                  container
                  spacing={1}
                  sx={{ width: "100%", height: "100%", mt: 1 }}
                >
                  <Grid item xs={6}>
                    <Label>Status :</Label>
                    <Typography>{details.response?.status}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Label>Exception : </Label>
                    <Typography>{details.response?.data.exception}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Label>Description : </Label>
                    <Typography sx={{ whiteSpace: "pre-wrap" }}>
                      {details.response?.data.description}
                    </Typography>
                  </Grid>
                </Grid>
              ) : (
                details.toString()
              )}
            </Paper>
          </Collapse>
        </Card>
      </Snackbar>
    );
  }
);

SnackErrorMessage.displayName = "SnackErrorMessage";

export default SnackErrorMessage;
