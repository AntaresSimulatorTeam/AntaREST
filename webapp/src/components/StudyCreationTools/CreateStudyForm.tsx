import React, { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { Button, Input, MenuItem, Select } from '@material-ui/core';
import debug from 'debug';
import { connect, ConnectedProps } from 'react-redux';
import { createStudy, getStudyMetadata } from '../../services/api/study';
import { addStudies, initStudiesVersion } from '../../ducks/study';
import { StudyMetadata } from '../../common/types';
import { AppState } from '../../App/reducers';
import { displayVersionName } from '../../services/utils';

const logErr = debug('antares:createstudyform:error');

interface Inputs {
  studyname: string;
  version: number;
}

const mapState = (state: AppState) => ({
  versions: state.study.versionList,
});

const mapDispatch = ({
  addStudy: (study: StudyMetadata) => addStudies([study]),
  loadVersions: initStudiesVersion,
});

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
interface OwnProps {
  useStyles: () => Record<'button' | 'root' | 'input', string>;
}
type PropTypes = PropsFromRedux & OwnProps;

const CreateStudyForm = (props: PropTypes) => {
  const [t] = useTranslation();
  const { useStyles, addStudy, loadVersions, versions } = props;
  const classes = useStyles();
  const { control, register, handleSubmit } = useForm<Inputs>();

  const onSubmit = async (data: Inputs) => {
    if (data.studyname) {
      try {
        const sid = await createStudy(data.studyname, data.version);
        const metadata = await getStudyMetadata(sid);
        addStudy(metadata);
      } catch (e) {
        logErr('Failed to create new study', data.studyname, e);
      }
    }
  };

  const defaultVersion = versions && versions[versions.length - 1];

  useEffect(() => {
    if (!versions) {
      loadVersions();
    }
  });

  return (
    <form className={classes.root} onSubmit={handleSubmit(onSubmit)}>
      <Button className={classes.button} type="submit" variant="contained" color="primary">{t('main:create')}</Button>
      <Input className={classes.input} placeholder={t('studymanager:nameofstudy')} inputProps={{ id: 'studyname', name: 'studyname', ref: register({ required: true }) }} />
      { defaultVersion && (
        <Controller
          name="version"
          control={control}
          defaultValue={defaultVersion}
          rules={{ required: true }}
          render={(field) => (
            <Select
              labelId="select-study-version-label"
              id="select-study-version"
              value={field.value}
              onChange={field.onChange}
            >
              { versions &&
              versions.map((versionName) => (
                <MenuItem value={versionName} key={versionName}>{displayVersionName(versionName)}</MenuItem>
              ))
            }
            </Select>
          )}
        />
      )}
    </form>
  );
};

export default connector(CreateStudyForm);
