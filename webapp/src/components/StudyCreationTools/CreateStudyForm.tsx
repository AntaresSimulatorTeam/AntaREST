import React from 'react';
import { Controller, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { Button, Input, MenuItem, Select } from '@material-ui/core';
import debug from 'debug';
import { connect, ConnectedProps } from 'react-redux';
import { createStudy, getStudyMetadata } from '../../services/api/study';
import { addStudies } from '../../ducks/study';
import { StudyMetadata } from '../../common/types';

const logErr = debug('antares:createstudyform:error');

const AVAILABLE_VERSIONS: Record<string, number> = {
  '8.0.3': 803,
  '7.2.0': 720,
  '7.1.0': 710,
  '7.0.0': 700,
  '6.1.3': 613,
};
const DEFAULT_VERSION = 803;

interface Inputs {
  studyname: string;
  version: number;
}

const mapState = () => ({ /* noop */ });

const mapDispatch = ({
  addStudy: (study: StudyMetadata) => addStudies([study]),
});

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
interface OwnProps {
  useStyles: () => Record<'button' | 'root' | 'input', string>;
}
type PropTypes = PropsFromRedux & OwnProps;

const CreateStudyForm = (props: PropTypes) => {
  const [t] = useTranslation();
  const { useStyles, addStudy } = props;
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

  return (
    <form className={classes.root} onSubmit={handleSubmit(onSubmit)}>
      <Button id="createstudysubmit" className={classes.button} type="submit" variant="contained" color="primary">{t('main:create')}</Button>
      <Input className={classes.input} placeholder={t('studymanager:nameofstudy')} inputProps={{ id: 'studyname', name: 'studyname', ref: register({ required: true }) }} />
      <Controller
        name="version"
        control={control}
        defaultValue={DEFAULT_VERSION}
        rules={{ required: true }}
        render={(field) => (
          <Select
            labelId="select-study-version-label"
            id="select-study-version"
            value={field.value}
            onChange={field.onChange}
          >
            {
            Object.keys(AVAILABLE_VERSIONS).map((versionName) => (
              <MenuItem value={AVAILABLE_VERSIONS[versionName]} key={versionName}>{versionName}</MenuItem>
            ))
          }
          </Select>
        )}
      />
    </form>
  );
};

export default connector(CreateStudyForm);
