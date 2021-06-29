import React from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { Button, Input } from '@material-ui/core';
import debug from 'debug';
import { connect, ConnectedProps } from 'react-redux';
import { createStudy, getStudyMetadata } from '../../services/api/study';
import { getStudyIdFromUrl } from '../../services/utils';
import { addStudies } from '../../ducks/study';
import { StudyMetadata } from '../../common/types';

const logErr = debug('antares:createstudyform:error');

interface Inputs {
  studyname: string;
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
  const { register, handleSubmit } = useForm<Inputs>();

  const onSubmit = async (data: Inputs) => {
    if (data.studyname) {
      try {
        const res = await createStudy(data.studyname);
        const sid = getStudyIdFromUrl(res);
        const metadata = await getStudyMetadata(sid);
        addStudy(metadata);
      } catch (e) {
        logErr('Failed to create new study', data.studyname, e);
      }
    }
  };

  return (
    <form className={classes.root} onSubmit={handleSubmit(onSubmit)}>
      <Button className={classes.button} type="submit" variant="outlined" color="primary">{t('main:create')}</Button>
      <Input className={classes.input} placeholder={t('studymanager:nameofstudy')} inputProps={{ id: 'studyname', name: 'studyname', ref: register({ required: true }) }} />
    </form>
  );
};

export default connector(CreateStudyForm);
