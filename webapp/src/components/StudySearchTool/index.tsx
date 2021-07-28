/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useForm, Controller } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { InputBase, makeStyles, Theme, createStyles, MenuItem, Select } from '@material-ui/core';
import { AppState } from '../../App/reducers';
import { StudyMetadata } from '../../common/types';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      marginTop: theme.spacing(1),
      marginBottom: theme.spacing(1),
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
      borderRadius: '4px',
      padding: theme.spacing(1),
      background: '#e6e6e6',
    },
    versioninput: {
      margin: theme.spacing(1),
      flex: '10% 0 0',
    },
  }));

interface Inputs {
  searchstring: string;
  versions: string[];
}

const mapState = (state: AppState) => ({
  studies: state.study.studies,
});

const mapDispatch = ({
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
interface OwnProps {
  setLoading: (isLoading: boolean) => void;
  setFiltered: (studies: StudyMetadata[]) => void;
}
type PropTypes = ReduxProps & OwnProps;

const StudySearchTool = (props: PropTypes) => {
  const { setLoading, setFiltered, studies } = props;
  const classes = useStyles();
  const [t] = useTranslation();
  const { register, handleSubmit, watch, control } = useForm<Inputs>({
    defaultValues: { versions: [] },
  });

  const filter = (studylist: StudyMetadata[], filters: Inputs): StudyMetadata[] => studylist
    .filter((s) => !filters.searchstring || s.name.search(new RegExp(filters.searchstring, 'i')) !== -1)
    .filter((s) => filters.versions.length === 0 || filters.versions.indexOf(s.version) !== -1);

  const onSubmit = async (data: Inputs) => {
    setLoading(true);
    setFiltered(filter(studies, data));
    setLoading(false);
  };

  useEffect(() => {
    setFiltered(filter(studies, watch()));
  }, [studies]);

  return (
    <div className={classes.root}>
      <form className={classes.form} onSubmit={handleSubmit(onSubmit)}>
        <InputBase
          className={classes.searchbar}
          placeholder={`${t('studymanager:searchstudy')}...`}
          onChange={() => onSubmit(watch())}
          inputProps={{
            'aria-label': 'search studies',
            ref: register,
            name: 'searchstring',
          }}
        />
        <Controller
          render={({ onChange, onBlur, value }) => (
            <Select
              className={classes.versioninput}
              multiple
              onChange={(e) => { onChange(e); onSubmit(watch()); }}
              onBlur={onBlur}
              value={value}
            >
              <MenuItem key="640" value="640">6.4.0</MenuItem>
              <MenuItem key="700" value="700">7.0.0</MenuItem>
              <MenuItem key="710" value="710">7.1.0</MenuItem>
              <MenuItem key="720" value="720">7.2.0</MenuItem>
              <MenuItem key="800" value="800">8.0.0</MenuItem>
            </Select>
          )}
          name="versions"
          defaultValue={[]}
          control={control}
        />
      </form>
    </div>
  );
};

export default connector(StudySearchTool);
