import React from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useForm, Controller } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { InputBase, makeStyles, Theme, createStyles, MenuItem, Select } from '@material-ui/core';
import { initStudies } from '../../ducks/study';
import { AppState } from '../../App/reducers';
import { getStudies } from '../../services/api/study';
import { StudyMetadata } from '../../common/types';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      marginTop: theme.spacing(1),
      marginBottom: theme.spacing(1),
      marginLeft: theme.spacing(3),
      marginRight: theme.spacing(3),
      display: 'flex',
      alignItems: 'center',
    },
    form: {
      width: '100%',
      display: 'flex',
      flexWrap: 'wrap',
    },
    searchbar: {
      flex: '100% 0 0',
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
  version: string;
}

const mapState = (state: AppState) => ({
  studies: state.study.studies,
});

const mapDispatch = ({
  loadStudies: initStudies,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
interface OwnProps {
  setLoading: (isLoading: boolean) => void;
}
type PropTypes = ReduxProps & OwnProps;

const StudySearchTool = (props: PropTypes) => {
  const { loadStudies, setLoading } = props;
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { register, handleSubmit, watch, control } = useForm<Inputs>({
    defaultValues: { version: '' },
  });

  const filter = (studylist: StudyMetadata[], filters: Inputs): StudyMetadata[] => studylist
    .filter((s) => !filters.searchstring || s.name.search(new RegExp(filters.searchstring, 'i')) !== -1)
    .filter((s) => !filters.version || s.version === filters.version);

  const onSubmit = async (data: Inputs) => {
    setLoading(true);
    try {
      const allStudies = await getStudies();
      loadStudies(filter(allStudies, data));
    } catch (e) {
      enqueueSnackbar(<div>{t('studymanager:failtoretrievestudies')}</div>, { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={classes.root}>
      <form className={classes.form} onSubmit={handleSubmit(onSubmit)}>
        <InputBase
          className={classes.searchbar}
          placeholder={`${t('studymanager:searchstudy')}...`}
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
              id="demo-simple-select"
              onChange={(e) => { onChange(e); onSubmit(watch()); }}
              onBlur={onBlur}
              value={value}
            >
              <MenuItem key="all" value="">--</MenuItem>
              <MenuItem key="640" value="640">6.4.0</MenuItem>
              <MenuItem key="700" value="700">7.0.0</MenuItem>
              <MenuItem key="710" value="710">7.1.0</MenuItem>
              <MenuItem key="720" value="720">7.2.0</MenuItem>
              <MenuItem key="800" value="800">8.0.0</MenuItem>
            </Select>
          )}
          name="version"
          defaultValue=""
          control={control}
        />
      </form>
    </div>
  );
};

export default connector(StudySearchTool);
