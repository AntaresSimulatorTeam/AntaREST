/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { InputBase, makeStyles, Theme, createStyles, Typography } from '@material-ui/core';
import moment from 'moment';
import { AppState } from '../../App/reducers';
import { GenericInfo, GroupDTO, StudyMetadata, UserDTO } from '../../common/types';
import { SortElement, SortItem } from '../ui/SortView/utils';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      marginTop: theme.spacing(1),
      marginBottom: theme.spacing(2),
      marginLeft: theme.spacing(3),
      marginRight: theme.spacing(2),
      display: 'flex',
      alignItems: 'center',
      flex: 1,
    },
    form: {
      width: '100%',
      display: 'flex',
      flexWrap: 'wrap',
      justifyContent: 'space-between',
    },
    searchbar: {
      flex: '80% 1 1',
      padding: theme.spacing(1),
      border: `2px solid ${theme.palette.primary.main}`,
    },
    versioninput: {
      margin: theme.spacing(1),
      minWidth: '200px',
      border: `2px solid ${theme.palette.primary.main}`,
      borderRadius: theme.shape.borderRadius,
      flex: '10% 0 0',
    },
    selectLabel: {
      marginBottom: theme.spacing(1),
      marginLeft: theme.spacing(1),
      boxSizing: 'border-box',
    },
    input: {
      paddingLeft: theme.spacing(1),
      border: '0px',
      backgroundColor: '#00000000',
      '&:hover': {
        border: '0px',
        backgroundColor: '#00000000',
      },
    },
    select: {
      border: '0px',
      paddingLeft: theme.spacing(1),
      backgroundColor: '#00000000',
      '&:hover': {
        border: 0,
        backgroundColor: '#00000000',
      },
    },
    counter: {
      marginLeft: theme.spacing(1),
      marginRight: theme.spacing(1),
      fontSize: '0.8em',
      fontStyle: 'italic',
      color: '#3e3e3e',
    },
  }));

const mapState = (state: AppState) => ({
  studies: state.study.studies,
});

const mapDispatch = ({
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
interface OwnProps {
  setLoading: (isLoading: boolean) => void;
  setFiltered: (studies: Array<StudyMetadata>) => void;
  sortItem: SortItem | undefined;
  sortList: Array<SortElement>;
  versionFilter: GenericInfo | undefined;
  userFilter: UserDTO | undefined;
  groupFilter: GroupDTO | undefined;
  filterManaged: boolean;
}
type PropTypes = ReduxProps & OwnProps;

const StudySearchTool = (props: PropTypes) => {
  const { filterManaged, setLoading, setFiltered, versionFilter, sortItem, sortList, studies, userFilter, groupFilter } = props;
  const classes = useStyles();
  const [t] = useTranslation();
  const [resultCount, setResultCount] = useState(studies.length);
  const [searchName, setSearchName] = useState<string>('');

  const sortStudies = (): Array<StudyMetadata> => {
    const tmpStudies: Array<StudyMetadata> = ([] as Array<StudyMetadata>).concat(studies);
    if (sortItem && sortItem.status !== 'NONE') {
      tmpStudies.sort((studyA: StudyMetadata, studyB: StudyMetadata) => {
        const firstElm = sortItem.status === 'INCREASE' ? studyA : studyB;
        const secondElm = sortItem.status === 'INCREASE' ? studyB : studyA;
        if (sortItem.element.id === sortList[0].id) {
          return firstElm.name.localeCompare(secondElm.name);
        }
        return (moment(firstElm.modificationDate).isAfter(moment(secondElm.modificationDate)) ? 1 : -1);
      });
    }
    return tmpStudies;
  };

  const filter = (currentName: string): StudyMetadata[] => sortStudies()
    .filter((s) => !currentName || (s.name.search(new RegExp(currentName, 'i')) !== -1) || (s.id.search(new RegExp(currentName, 'i')) !== -1))
    .filter((s) => !versionFilter || versionFilter.id === s.version)
    .filter((s) => (userFilter ? (s.owner.id && userFilter.id === s.owner.id) : true))
    .filter((s) => (groupFilter ? s.groups.findIndex((elm) => elm.id === groupFilter.id) >= 0 : true))
    .filter((s) => (filterManaged ? s.managed : true));

  const onChange = async (currentName: string) => {
    setLoading(true);
    const f = filter(currentName);
    setFiltered(f);
    setResultCount(f.length);
    setLoading(false);
    if (currentName !== searchName) setSearchName(currentName);
  };

  useEffect(() => {
    const f = filter(searchName);
    setFiltered(f);
    setResultCount(f.length);
  }, [studies, sortItem, userFilter, groupFilter, versionFilter, filterManaged]);

  return (
    <div className={classes.root}>
      <InputBase
        className={classes.searchbar}
        placeholder={`${t('studymanager:searchstudy')}...`}
        onChange={(e) => onChange(e.target.value as string)}
        inputProps={{
          'aria-label': 'search studies',
          name: 'searchstring',
        }}
      />
      <Typography className={classes.counter}>
        {`(${resultCount})`}
      </Typography>
    </div>
  );
};

export default connector(StudySearchTool);
