/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { InputBase, makeStyles, Theme, createStyles, MenuItem, Select, FormControl, InputLabel, Input, Checkbox, ListItemText } from '@material-ui/core';
import moment from 'moment';
import { AppState } from '../../App/reducers';
import { GroupDTO, StudyMetadata, UserDTO } from '../../common/types';
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
  userFilter: UserDTO | undefined;
  groupFilter: GroupDTO | undefined;
  filterManaged: boolean;
}
type PropTypes = ReduxProps & OwnProps;

const StudySearchTool = (props: PropTypes) => {
  const { filterManaged, setLoading, setFiltered, sortItem, sortList, studies, userFilter, groupFilter } = props;
  const classes = useStyles();
  const [t] = useTranslation();
  const [versions, setVersions] = useState<Array<string>>([]);
  const [searchName, setSearchName] = useState<string>('');

  const versionList = [{ key: '640', value: '6.4.0' },
    { key: '700', value: '7.0.0' },
    { key: '710', value: '7.1.0' },
    { key: '720', value: '7.2.0' },
    { key: '800', value: '8.0.0' }];

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

  const filter = (currentName: string, currentVersions: Array<string>): StudyMetadata[] => sortStudies()
    .filter((s) => !currentName || s.name.search(new RegExp(currentName, 'i')) !== -1)
    .filter((s) => currentVersions.length === 0 || currentVersions.indexOf(s.version) >= 0)
    .filter((s) => (userFilter ? (s.owner.id && userFilter.id === s.owner.id) : true))
    .filter((s) => (groupFilter ? s.groups.findIndex((elm) => elm.id === groupFilter.id) >= 0 : true))
    .filter((s) => (filterManaged ? s.managed : true));

  const onChange = async (currentName: string, currentVersions: Array<string>) => {
    setLoading(true);
    const f = filter(currentName, currentVersions);
    setFiltered(f);
    setLoading(false);
    if (currentName !== searchName) setSearchName(currentName);
    if (currentVersions !== versions) setVersions(currentVersions);
  };

  useEffect(() => {
    const f = filter(searchName, versions);
    setFiltered(f);
  }, [studies, sortItem, userFilter, groupFilter, filterManaged]);

  return (
    <div className={classes.root}>
      <InputBase
        className={classes.searchbar}
        placeholder={`${t('studymanager:searchstudy')}...`}
        onChange={(e) => onChange(e.target.value as string, versions)}
        inputProps={{
          'aria-label': 'search studies',
          name: 'searchstring',
        }}
      />
      <FormControl className={classes.versioninput}>
        <InputLabel className={classes.selectLabel} id="versions">{t('studymanager:versionLabel')}</InputLabel>
        <Select
          labelId="versions"
          id="version-checkbox"
          multiple
          value={versions}
          onChange={(e) => onChange(searchName, e.target.value as Array<string>)}
          input={<Input className={classes.input} />}
          renderValue={(selected) => (selected as Array<string>).join(', ')}
          className={classes.select}
        >
          {versionList.map((elm) => (
            <MenuItem key={elm.value} value={elm.key}>
              <Checkbox checked={versions.indexOf(elm.key) > -1} />
              <ListItemText primary={elm.value} />
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </div>
  );
};

export default connector(StudySearchTool);
