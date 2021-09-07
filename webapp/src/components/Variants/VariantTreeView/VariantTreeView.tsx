import { createStyles, makeStyles, useTheme } from '@material-ui/core';
import React, { useCallback, useEffect, useState } from 'react';
import { useHistory } from 'react-router-dom';
import Tree from 'react-d3-tree';
import { CustomNodeElementProps, Point, RawNodeDatum } from 'react-d3-tree/lib/types/common';
import { StudyMetadata } from '../../../common/types';
import VariantCard from './VariantCard';
import { buildNodeFromMetadata, buildTree } from './utils';

const debugData: Array<RawNodeDatum> = [
  {
    name: '',
    attributes: {
      title: 'Card title',
      subtitle: 'Card subtitle',
      text: 'Some text to build on the card.',
      date: '10/08/2018',
    },
    children: [
      {
        name: '',
        attributes: {
          title: 'Card title',
          subtitle: 'Card subtitle',
          text: 'Some text to build on the card.',
          date: '10/08/2018',
        },
        children: [
          {
            name: 'child2',
            attributes: {
              title: 'child2',
              subtitle: 'Card subtitle',
              text: 'Some text to build on the card.',
              date: '10/08/2018',
            },
          },
          {
            name: 'child2',
            attributes: {
              title: 'child3',
              subtitle: 'Card subtitle',
              text: 'Some text to build on the card.',
              date: '10/08/2018',
            },
          },
        ],
      },
      {
        name: '',
        attributes: {
          title: 'Card title',
          subtitle: 'Card subtitle',
          text: 'Some text to build on the card.',
          date: '10/08/2018',
        },
      },
      {
        name: '',
        attributes: {
          title: 'Card title',
          subtitle: 'Card subtitle',
          text: 'Some text to build on the card.',
        },
      },
    ],
  },
];

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
    // Build the graph
    const init = async () => {
      if (study === undefined) return;
      try {
        const rootNode = buildNodeFromMetadata(study);
        await buildTree(rootNode);
        setData([{ ...rootNode }]);
      } catch (e) {
        console.log(e);
      }
    };
    init();
    // setData(debugData);
  }, [study]);

  return (
    <div className={classes.root} ref={treeContainer}>
      {
          data !== undefined && data.length > 0 && (
          <Tree
            data={data}
            collapsible={false}
            translate={translate}
            scaleExtent={{ min: 1, max: 3 }}
            pathFunc="elbow"
            orientation="vertical"
            nodeSize={{ x: 300, y: yClearance }}
            renderCustomNodeElement={(rd3tProps: CustomNodeElementProps) =>
              VariantCard({ rd3tProps, theme, history })
            }
          />
          )
      }
    </div>
  );
};

export default VariantTreeView;
