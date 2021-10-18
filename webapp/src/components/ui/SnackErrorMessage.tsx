/* eslint-disable quote-props */
import React, { useState, forwardRef, useCallback } from 'react';
import classnames from 'classnames';
import { makeStyles } from '@material-ui/core/styles';
import { useSnackbar, SnackbarContent } from 'notistack';
import Collapse from '@material-ui/core/Collapse';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';
import Card from '@material-ui/core/Card';
import CardActions from '@material-ui/core/CardActions';
import IconButton from '@material-ui/core/IconButton';
import CloseIcon from '@material-ui/icons/Close';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import CancelIcon from '@material-ui/icons/Cancel';
import Grid from '@material-ui/core/Grid';
import { AxiosError } from 'axios';

const useStyles = makeStyles((theme) => ({
  root: {
    [theme.breakpoints.up('sm')]: {
      minWidth: '344px !important',
    },
  },
  card: {
    backgroundColor: theme.palette.error.main,
    width: '100%',
    color: 'white',
  },
  typography: {

  },
  actionRoot: {
    padding: '8px 8px 8px 16px',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  icons: {
    marginLeft: 'auto',
  },
  expand: {
    padding: '8px 8px',
    transform: 'rotate(0deg)',
    color: 'white',
    transition: theme.transitions.create('transform', {
      duration: theme.transitions.duration.shortest,
    }),
  },
  expandOpen: {
    transform: 'rotate(180deg)',
  },
  collapse: {
    padding: 16,
  },
  checkIcon: {
    fontSize: 20,
    color: 'white',
    paddingRight: 4,
  },
  button: {
    padding: 0,
    textTransform: 'none',
  },
  details: {
    width: '100%',
    height: '100%',
    marginTop: theme.spacing(1),
  },
  label: {
    fontWeight: 'bold',
    color: theme.palette.primary.main,
    marginRight: theme.spacing(1),
  },
  errorMessage: {
    color: theme.palette.primary.main,
  },
}));

interface Props {
  id: string | number;
  message: string | React.ReactNode;
  details: AxiosError;
}

const SnackErrorMessage = forwardRef<HTMLDivElement, Props>((props: Props, ref) => {
  const classes = useStyles();
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
    <SnackbarContent ref={ref} className={classes.root}>
      <Card className={classes.card}>
        <CardActions classes={{ root: classes.actionRoot }}>
          <CancelIcon style={{ width: '20px', height: '20px' }} />
          <Typography variant="subtitle2" className={classes.typography}>{message}</Typography>
          <div className={classes.icons}>
            <IconButton
              aria-label="Show more"
              className={classnames(classes.expand, { [classes.expandOpen]: expanded })}
              onClick={handleExpandClick}
            >
              <ExpandMoreIcon />
            </IconButton>
            <IconButton className={classes.expand} onClick={handleDismiss}>
              <CloseIcon />
            </IconButton>
          </div>
        </CardActions>
        {
          details.response !== undefined && (
          <Collapse in={expanded} timeout="auto" unmountOnExit>
            <Paper className={classes.collapse}>
              <Grid container spacing={1} className={classes.details}>
                <Grid item xs={6}>
                  <Typography className={classes.label}>Status :</Typography>
                  <Typography className={classes.errorMessage}>{details.response.status}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography className={classes.label}>Exception : </Typography>
                  <Typography className={classes.errorMessage}>{details.response.data.exception}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography className={classes.label}>Description : </Typography>
                  <Typography className={classes.errorMessage}>{details.response.data.description}</Typography>
                </Grid>
              </Grid>
            </Paper>
          </Collapse>
          )}
      </Card>
    </SnackbarContent>
  );
});

export default SnackErrorMessage;
