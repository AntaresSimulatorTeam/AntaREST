import React, { useEffect, useState } from 'react';
import { createStyles, makeStyles } from '@material-ui/core';
import { useHistory } from 'react-router-dom';
import { Components, StudyMetadata } from '../../common/types';
import VariantNav from './VariantNavSwitch';
import VariantTreeView from './VariantTreeView';
import EditionView from './Edition';

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
  const items: Components = {
    'variants:variantDependencies': () => <VariantTreeView study={study} />,
    'variants:editionMode': () => <EditionView studyId={study !== undefined ? study.id : ''} />,
    //    'variants:testGeneration': () => <div style={{ width: '100%', height: '100%' }}>Test generation</div>,
  };
  const classes = useStyles();
  const [navState, setNavState] = useState<string>(option === 'edition' && study?.type === 'variantstudy' ? 'variants:editionMode' : 'variants:variantDependencies');
  const [editionMode, setEditionMode] = useState<boolean>(option === 'edition');

  const onItemClick = (item: string) => {
    setNavState(item);
  };

  useEffect(() => {
    // we add a check on study type because when creating a new variant the option is set to edition
    // but the parent component has not already fetched/set the study object, so there is a first render with the parent study object and edit option on
    setEditionMode(option === 'edition' && study?.type === 'variantstudy');
    setNavState(option === 'edition' && study?.type === 'variantstudy' ? 'variants:editionMode' : 'variants:variantDependencies');
  }, [option, study]);

  const onEditModeChange = () => {
    if (editionMode) {
      setNavState('variants:variantDependencies');
      history.replace(`/study/${study !== undefined ? study.id : ''}/variants`);
    } else {
      history.replace(`/study/${study !== undefined ? study.id : ''}/variants/edition`);
      setNavState('variants:editionMode');
    }
    setEditionMode(!editionMode);
  };

  return (
    <div className={classes.root}>
      <VariantNav
        currentItem={navState}
        editionMode={editionMode}
        onItemClick={onItemClick}
        onEditModeChange={onEditModeChange}
        studyId={study !== undefined ? study.id : ''}
        editable={study !== undefined ? study.type === 'variantstudy' : false}
      />
      { items[navState]() }
    </div>
  );
};

export default VariantView;
