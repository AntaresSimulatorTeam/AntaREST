import React, { useEffect, useState } from 'react';
import { createStyles, makeStyles } from '@material-ui/core';
import { useHistory } from 'react-router-dom';
import { Components, StudyMetadata } from '../../common/types';
import VariantTreeView from './VariantTreeView';
import EditionView from './Edition';
import GenericNavView from '../ui/NavComponents/GenericNavView';

const useStyles = makeStyles(() => createStyles({
  root: {
    height: '100%',
    width: '100%',
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
  },
}));

interface PropTypes {
    // eslint-disable-next-line react/require-default-props
    option: string | undefined;
    study: StudyMetadata | undefined;
}

const VariantView = (props: PropTypes) => {
  const { option = '', study } = props;
  const history = useHistory();

  const classes = useStyles();
  const [editionMode, setEditionMode] = useState<boolean>(false);
  const [items, setItems] = useState<Components>({
    'variants:variantDependencies': () => <VariantTreeView study={study} />,
  });

  useEffect(() => {
    // we add a check on study type because when creating a new variant the option is set to edition
    // but the parent component has not already fetched/set the study object, so there is a first render with the parent study object and edit option on
    const edition = option === 'edition' && study?.type === 'variantstudy';
    setEditionMode(edition);
  }, [option, study]);

  useEffect(() => {
    setItems(study?.type === 'variantstudy' ? {
      'variants:variantDependencies': () => <VariantTreeView study={study} />,
      'variants:editionMode': () => <EditionView studyId={study !== undefined ? study.id : ''} />,
    } : {
      'variants:variantDependencies': () => <VariantTreeView study={study} />,
    });
  }, [study]);

  const onEditModeChange = (item: string) => {
    if (item === 'variants:variantDependencies') {
      history.replace(`/study/${study !== undefined ? study.id : ''}/variants`);
    } else {
      history.replace(`/study/${study !== undefined ? study.id : ''}/variants/edition`);
    }
  };

  return (
    <div className={classes.root}>
      <GenericNavView
        items={items}
        initialValue={editionMode ? 'variants:editionMode' : 'variants:variantDependencies'}
        onClick={onEditModeChange}
      />
    </div>
  );
};

export default VariantView;
