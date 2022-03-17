import React from 'react';
import { makeStyles, createStyles, Theme, Paper, TableContainer, Table, TableHead, TableRow, TableCell, TableBody } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import { JobsType } from './types';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flexGrow: 1,
    marginLeft: theme.spacing(1),
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(2),
    marginBottom: theme.spacing(2),
    overflow: 'auto',
  },
  table: {
    width: '100%',
    height: '100%',
  },
}));

interface PropType {
    content: Array<JobsType>;
}

const JobTableView = (props: PropType) => {
  const { content } = props;
  const [t] = useTranslation();
  const classes = useStyles();

  return (
    <Paper className={classes.root} elevation={1}>
      <TableContainer component={Paper}>
        <Table className={classes.table} aria-label="simple table">
          <TableHead>
            <TableRow>
              <TableCell>Tâches</TableCell>
              <TableCell align="right">Type</TableCell>
              <TableCell align="right">{t('main:date')}</TableCell>
              <TableCell align="right">Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {content.map((row) => (
              <TableRow>
                <TableCell component="th" scope="row">
                  {row.name}
                </TableCell>
                <TableCell align="right">{t(`jobs:${row.type}`)}</TableCell>
                <TableCell align="right">{row.dateView}</TableCell>
                <TableCell align="right">{row.action}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default JobTableView;
