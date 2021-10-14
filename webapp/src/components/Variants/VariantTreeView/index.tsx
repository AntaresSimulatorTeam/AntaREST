import { Button, createStyles, makeStyles, useTheme } from '@material-ui/core';
import debug from 'debug';
import React, { useCallback, useEffect, useState } from 'react';
import { useSnackbar } from 'notistack';
import { AxiosError } from 'axios';
import { useHistory } from 'react-router-dom';
import Tree from 'react-d3-tree';
import { CustomNodeElementProps, Point, RawNodeDatum } from 'react-d3-tree/lib/types/common';
import { useTranslation } from 'react-i18next';
import { StudyMetadata } from '../../../common/types';
import VariantCard from './VariantCard';
import { getTreeNodes } from './utils';
import CreateVariantModal from '../CreateVariantModal';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';

const logError = debug('antares:varianttree:error');

const useStyles = makeStyles(() => createStyles({
  root: {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
  },
  header: {
    width: '100%',
    height: '60px',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  tree: {
    width: '100%',
    flex: 1,
  },
  cardBody: {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
  },
}));

interface PropsType {
    study: StudyMetadata | undefined;
}

const VariantTreeView = (props: PropsType) => {
  const yOffset = 150;
  const yClearance = 250;
  const { study } = props;
  const [translate, setTranslte] = useState<Point>({ x: 0, y: 0 });
  const [data, setData] = useState<RawNodeDatum[]>([]);
  const [openModal, setOpenModal] = useState<boolean>(false);
  const classes = useStyles();
  const theme = useTheme();
  const { enqueueSnackbar } = useSnackbar();
  const [t] = useTranslation();
  const history = useHistory();
  const treeContainer = useCallback((node) => {
    if (node !== null) {
      const dimensions = node.getBoundingClientRect();
      setTranslte({
        x: dimensions.width / 2,
        y: yOffset,
      });
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      if (study === undefined) return;
      try {
        const rootNode = await getTreeNodes(study);
        setData([{ ...rootNode }]);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('variants:fetchTreeDataError'), e as AxiosError);
        logError('Failed to fetch tree data', e);
      }
    };
    init();
    return () => setData([]);
  }, [enqueueSnackbar, study, t]);

  return (
    <div className={classes.root}>
      <div className={classes.header}>
        <Button color="primary" variant="outlined" style={{ margin: theme.spacing(0, 3) }} onClick={() => setOpenModal(true)}>
          {t('variants:createVariant')}
        </Button>
      </div>
      <div className={classes.tree} ref={treeContainer}>
        {
          data !== undefined && data.length > 0 && (
          <Tree
            data={data}
            collapsible={false}
            translate={translate}
            scaleExtent={{ min: 0, max: 3 }}
            pathFunc="elbow"
            orientation="vertical"
            nodeSize={{ x: 300, y: yClearance }}
            renderCustomNodeElement={(rd3tProps: CustomNodeElementProps) =>
              VariantCard({ rd3tProps, theme, history, studyId: study !== undefined ? study.id : '' })
            }
          />
          )
      }
      </div>
      <CreateVariantModal open={openModal} onClose={() => setOpenModal(false)} parentId={study !== undefined ? study.id : ''} />
    </div>
  );
};

export default VariantTreeView;
