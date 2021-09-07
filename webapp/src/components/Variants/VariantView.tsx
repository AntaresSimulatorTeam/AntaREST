import React, { useState } from 'react';
import { createStyles, makeStyles } from '@material-ui/core';
import { Components, StudyMetadata } from '../../common/types';
import VariantNav from './VariantNavSwitch';
import VariantTreeView from './VariantTreeView/VariantTreeView';

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
    initEditMode?: boolean;
    // eslint-disable-next-line react/require-default-props
    editable?: boolean;
    study: StudyMetadata | undefined;
}

const VariantView = (props: PropTypes) => {
  const { editable = false, initEditMode = false, study } = props;
  const items: Components = {
    'singlestudy:variantDependencies': () => <VariantTreeView study={study} />,
    'singlestudy:createVariant': () => <div style={{ width: '100%', height: '100%' }}>Create variant</div>,
    'singlestudy:editionMode': () => <div style={{ width: '100%', height: '100%' }}>Edition variant</div>,
    'singlestudy:testGeneration': () => <div style={{ width: '100%', height: '100%' }}>Test generation</div>,
  };
  const classes = useStyles();
  const [navState, setNavState] = useState<string>(initEditMode ? 'singlestudy:editionMode' : 'singlestudy:variantDependencies');
  const [editionMode, setEditionMode] = useState<boolean>(initEditMode);

  const onItemClick = (item: string) => {
    setNavState(item);
  };

  const onEditModeChange = () => {
    if (editionMode) setNavState('singlestudy:variantDependencies');
    else setNavState('singlestudy:editionMode');
    setEditionMode(!editionMode);
  };

  return (
    <div className={classes.root}>
      <VariantNav
        currentItem={navState}
        editionMode={editionMode}
        onItemClick={onItemClick}
        onEditModeChange={onEditModeChange}
        editable={editable}
      />
      { items[navState]() }
    </div>
  );
};

export default VariantView;
