import React, { useState, useEffect } from 'react';
import moment from 'moment';
import { makeStyles, createStyles, Theme, Paper, TableContainer, Table, TableHead, TableRow, TableCell, TableBody, Box, FormControl, InputLabel, Select, MenuItem } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import ArrowDropUpIcon from '@material-ui/icons/ArrowDropUp';
import ArrowDropDownIcon from '@material-ui/icons/ArrowDropDown';
import { JobsType, TaskType } from './types';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flexGrow: 1,
    marginLeft: theme.spacing(1),
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(2),
    marginBottom: theme.spacing(2),
    overflowX: 'hidden',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
  },
  table: {
    width: '100%',
    height: '90%',
  },
  columnNames: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-end',
  },
  filterIcon: {
    cursor: 'pointer',
  },
  formControl: {
    margin: theme.spacing(1),
    marginRight: theme.spacing(3),
    minWidth: 160,
  },
  selectEmpty: {
    marginTop: theme.spacing(2),
  },
}));

interface PropType {
    content: Array<JobsType>;
}

const JobTableView = (props: PropType) => {
  const { content } = props;
  const [t] = useTranslation();
  const classes = useStyles();
  const [sorted, setSorted] = useState<string>();
  const [type, setType] = React.useState('');
  const [currentContent, setCurrentContent] = useState<JobsType[]>();

  const handleChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setType(event.target.value as string);
  };

  useEffect(() => {
    if (content) {
      if (type) {
        setCurrentContent(content.filter((o) => o.type === type));
      } else {
        setCurrentContent(content);
      }
    }
  }, [content, type]);

  const filterList = [
    'all',
    TaskType.DOWNLOAD,
    TaskType.LAUNCH,
    TaskType.COPY,
    TaskType.ARCHIVE,
    TaskType.UNARCHIVE,
  ];

  return (
    <Box className={classes.root}>
      <FormControl variant="outlined" className={classes.formControl}>
        <InputLabel id="jobsView-select-outlined-label">{t('jobs:typeFilter')}</InputLabel>
        <Select
          labelId="jobsView-select-outlined-label"
          id="jobsView-select-outlined"
          value={type}
          onChange={handleChange}
          label={t('jobs:typeFilter')}
        >
          {filterList.map((item) =>
            (
              <MenuItem value={item === 'all' ? '' : item} key={item}>
                {t(`jobs:${item}`)}
              </MenuItem>
            ))}
        </Select>
      </FormControl>
      <TableContainer component={Paper}>
        <Table className={classes.table} aria-label="simple table">
          <TableHead>
            <TableRow>
              <TableCell>
                {t('main:jobs')}
              </TableCell>
              <TableCell align="right">
                {t('singlestudy:type')}
              </TableCell>
              <TableCell align="right">
                <Box className={classes.columnNames}>
                  {t('main:date')}
                  {!sorted ? (<ArrowDropUpIcon className={classes.filterIcon} onClick={() => setSorted('date')} color="primary" />) : (
                    <ArrowDropDownIcon className={classes.filterIcon} onClick={() => setSorted(undefined)} color="primary" />)}
                </Box>
              </TableCell>
              <TableCell align="right">
                {t('jobs:action')}
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {!sorted && (sorted !== 'date') && currentContent ? currentContent.sort((a, b) => (moment(a.date).isAfter(moment(b.date)) ? -1 : 1)).map((row) => (
              <TableRow>
                <TableCell component="th" scope="row">
                  {row.name}
                </TableCell>
                <TableCell align="right">{t(`jobs:${row.type}`)}</TableCell>
                <TableCell align="right">{row.dateView}</TableCell>
                <TableCell align="right">{row.action}</TableCell>
              </TableRow>
            )) : (currentContent && currentContent.sort((a, b) => (moment(a.date).isAfter(moment(b.date)) ? 1 : -1)).map((row) => (
              <TableRow>
                <TableCell component="th" scope="row">
                  {row.name}
                </TableCell>
                <TableCell align="right">{t(`jobs:${row.type}`)}</TableCell>
                <TableCell align="right">{row.dateView}</TableCell>
                <TableCell align="right">{row.action}</TableCell>
              </TableRow>
            )))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default JobTableView;
