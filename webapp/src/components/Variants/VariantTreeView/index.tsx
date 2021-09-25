import { createStyles, makeStyles, useTheme } from '@material-ui/core';
import debug from 'debug';
import React, { useCallback, useEffect, useState } from 'react';
import { useHistory } from 'react-router-dom';
import Tree from 'react-d3-tree';
import { CustomNodeElementProps, Point, RawNodeDatum } from 'react-d3-tree/lib/types/common';
import { StudyMetadata } from '../../../common/types';
import VariantCard from './VariantCard';
import { getTreeNodes } from './utils';

const logError = debug('antares:varianttree:error');

const useStyles = makeStyles(() => createStyles({
  root: {
    width: '100%',
    height: '100%',
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
  const classes = useStyles();
  const theme = useTheme();
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
        logError('Failed to fetch tree data', e);
      }
    };
    init();
  }, [study]);

  return (
    <div className={classes.root} ref={treeContainer}>
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
  );
};

export default VariantTreeView;
